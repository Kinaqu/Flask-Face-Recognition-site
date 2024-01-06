from flask import Blueprint, render_template, request, url_for, session, jsonify, flash, send_from_directory
from flask.helpers import redirect
from . import db, bcrypt
from .models import User, ProfileInfo
import os
import cv2
from flask_bcrypt import Bcrypt, check_password_hash
from flask_login import login_user, login_required, current_user, logout_user
import logging
import numpy as np
import face_recognition
from io import BytesIO
from PIL import Image
import base64
from datetime import datetime

auth_signup = Blueprint('auth_signup', __name__)
auth_login = Blueprint('auth_login', __name__)
auth_profile = Blueprint('auth_profile', __name__)
auth_compare = Blueprint('auth_compare', __name__)


bcrypt = Bcrypt()


@auth_signup.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        image_data_url = request.form['image']

        webcam_image = process_image_data_url(image_data_url)

        save_directory = os.path.join(os.getcwd(), "captured_faces")
        os.makedirs(save_directory, exist_ok=True)

        image_name = f"image_{username}.jpg"
        image_path = os.path.join(save_directory, image_name)

        cv2.imwrite(image_path, webcam_image)

        with open(image_path, 'rb') as f:
            face_image_blob = f.read()

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, password=hashed_password, face_image=face_image_blob)
        db.session.add(user)
        db.session.commit()

        profile_info = ProfileInfo(user_id=user.id, birth_date=None, position=None, experience=None, email=None)
        db.session.add(profile_info)
        db.session.commit()

        # Сохранение пустого изображения для профиля
        profile_directory = os.path.join(os.getcwd(), "website/static/uploads/photo")
        os.makedirs(profile_directory, exist_ok=True)

        profile_image_name = f"profile_{username}.jpg"
        profile_image_path = os.path.join(profile_directory, profile_image_name)

        # Создание пустого изображения
        height, width, _ = webcam_image.shape  # получение размеров изображения с веб-камеры
        empty_image = 255 * np.ones((height, width, 3), dtype=np.uint8)  # создание пустого изображения

        cv2.imwrite(profile_image_path, empty_image)

        login_user(user)
        flash('Регистрация прошла успешно!', 'success')

    return render_template('register.html')


def process_image_data_url(image_data_url):
    try:
        if not image_data_url:
            raise ValueError("Image data URL is empty")

        _, encoded = image_data_url.split(',')
        image_data = BytesIO(base64.b64decode(encoded))
        img = Image.open(image_data)
        img_array = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        return img_array

    except ValueError as ve:
        logging.error(f"ValueError processing image data URL: {ve}")
    except Exception as e:
        logging.error(f"Error processing image data URL: {e}")

    return None


@auth_login.route('/get_user_data', methods=['POST'])
def get_user_data():
    data = request.get_json()
    username = data.get('username')
    user = User.query.filter_by(username=username).first()

    if user:
        # Сохраняем данные пользователя в сессии
        session['user_data'] = {
            'user_id': user.id,
            'username': user.username,
            'password': user.password,
        }

        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'User not found'}), 404



@auth_login.route('/uploads/photo/<path:filename>', methods=['GET'])
def get_uploaded_file(filename):
    return send_from_directory('uploads', filename)



@auth_login.route('/get_face_image', methods=['POST'])
def get_face_image():
    # Получаем изображение с фронтенда
    user_image_data = request.files.get('user_image')
    if not user_image_data:
        return jsonify({"error": "No image provided"}), 400
    
    # Получаем данные пользователя из сессии
    user_data = session.get('user_data')
    if not user_data:
        return jsonify({"error": "User data not found in session"}), 400
    
    user_id = user_data.get('user_id')
    
    # Получаем имя пользователя из базы данных
    user = User.query.get(user_id)
    if not user or not user.username:
        return jsonify({"error": "User or username not found"}), 400
    
    # Формируем полный путь к изображению в папке uploads
    upload_path = os.path.join('website/uploads', f'upload_{user.username}.jpg')
    upload_full_path = os.path.abspath(upload_path)  # Полный путь к изображению
    
    # Сохраняем изображение из фронтенда
    user_image_data.save(upload_full_path)

    # Формируем путь к изображению лица пользователя в папке captured_faces
    captured_face_path = os.path.join('captured_faces', f'image_{user.username}.jpg')

    # Загружаем и обрабатываем изображения с помощью face_recognition
    user_face_encoding = face_recognition.face_encodings(face_recognition.load_image_file(captured_face_path))[0]
    unknown_face_encoding = face_recognition.face_encodings(face_recognition.load_image_file(upload_full_path))[0]

    # Устанавливаем пороговое значение (чем ниже значение, тем строже сравнение)
    threshold = 0.6 

    # Сравниваем лица с учетом порогового значения
    distance = face_recognition.face_distance([user_face_encoding], unknown_face_encoding)
    if distance[0] < threshold:
        os.remove(upload_full_path)
        return jsonify({"match": True, "message": "Face matched successfully"}), 200
    else:
        # Переименовать изображение при неудачном сравнении
        restricted_path = os.path.join('website/static/uploads', f'upload_{user.username}_restricted.jpg')

        # Проверяем, существует ли уже ограниченное изображение
        count = 1
        while os.path.exists(restricted_path):
            # Создаем новое уникальное имя для файла
            restricted_path = os.path.join('website/static/uploads', f'upload_{user.username}_restricted({count}).jpg')
            count += 1

        # Переименовываем изображение
        os.rename(upload_full_path, os.path.abspath(restricted_path))
        return jsonify({"match": False, "message": "Face did not match"}), 200  
    

    

@auth_login.route('/get_password', methods=['POST'])
def get_password():
    # Пример получения пароля
    password = request.json.get('password')

    # Используйте данные из сессии, если они доступны
    user_data = session.get('user_data')

    if user_data:
        user_id = user_data.get('user_id')
        user = User.query.get(user_id)

        if user and check_password_hash(user.password, password):
            login_user(user)
    
    return jsonify({'status': 'error', 'message': 'Password mismatch'})


@auth_login.route('/login')
def login():
    return render_template('login.html')

@auth_profile.route('/profile')
@login_required
def profile():
    user = current_user
    profile_info = ProfileInfo.query.filter_by(user_id=user.id).first()
    
    # Определяем путь к папке с изображениями
    images_path = os.path.join(os.getcwd(), 'website', 'static', 'uploads')
    
    # Получаем список всех файлов в папке
    files = os.listdir(images_path)
    
    # Отбираем только файлы, являющиеся изображениями
    image_list = [file for file in files if file.endswith(('.jpg'))]
    
    profile_image_filename = f"profile_{user.username}.jpg"
    
    return render_template('profile.html', user=user, profile_info=profile_info, profile_image_filename=profile_image_filename, image_list=image_list)


@auth_profile.route('/update_profile', methods=['PUT'])
def update_profile():
    data = request.json
    if not data:
        return jsonify({'success': False, 'message': 'Отсутствуют данные для обновления'}), 400

    user = current_user
    profile = ProfileInfo.query.filter_by(user_id=user.id).first()
    
    if not profile:
        return jsonify({'success': False, 'message': 'Профиль не найден'}), 404

    # Обновление данных профиля
    fields_to_update = ['birth_date', 'position', 'experience', 'email']
    for field in fields_to_update:
        value = data.get(field)
        
        # Проверка и преобразование для даты
        if field == 'birth_date' and value:
            try:
                value = datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                return jsonify({'success': False, 'message': f'Неправильный формат даты для {field}'}), 400
        
        # Проверка и преобразование для опыта
        elif field == 'experience' and value:
            try:
                value = int(value)
            except ValueError:
                return jsonify({'success': False, 'message': f'Неправильный формат опыта для {field}'}), 400

        if value is not None:
            setattr(profile, field, value)

    try:
        db.session.commit()
        return jsonify({'success': True, 'message': 'Профиль успешно обновлен'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@auth_profile.route('/update_profile_image', methods=['PUT'])
@login_required
def update_profile_image():
    user = current_user

    if 'profile_image' in request.files:
        file = request.files['profile_image']

        if file.filename != '':
            filename = f"profile_{user.username}.jpg"
            file.save(os.path.join('website/static/uploads/photo', filename))

            flash('Profile image updated successfully!', 'success')
            return "Profile image updated successfully!", 200
        else:
            return "No file selected!", 400

    return "Invalid request!", 400

    


@auth_profile.route('/change_password', methods=['PUT'])
@login_required
def change_password():
    user = current_user
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')

    # Проверка старого пароля
    if not bcrypt.check_password_hash(user.password, old_password):
        flash('Incorrect old password!', 'error')
        return "Incorrect old password!", 400

    # Обновление пароля
    user.password = bcrypt.generate_password_hash(new_password)
    db.session.commit()

    flash('Password changed successfully!', 'success')
    return "Password changed successfully!", 200
    


@auth_profile.route('/delete_account', methods=['DELETE'])
@login_required
def delete_account():
    user = current_user

    # Удаление фотографии пользователя
    image_name = f"image_{user.username}.jpg"
    image_path = os.path.join(os.getcwd(), "captured_faces", image_name)
    image_profile = f"profile_{user.username}.jpg"
    profile_path = os.path.join(os.getcwd(), "website/static/uploads/photo", image_profile)
    if os.path.exists(image_path):
        os.remove(image_path)
        if os.path.exists(profile_path):
            os.remove(profile_path)


    # Удаление данных пользователя из базы данных
    db.session.delete(user)
    db.session.commit()

    flash('Your account has been deleted.', 'success')
    return "Your account has been deleted.", 200
    
    
@auth_profile.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth_profile.profile'))



@auth_profile.route('/try_compare', methods=['POST'])
def try_compare():
    try:
        # Получаем изображения с фронтенда
        canvas_image_data = request.files.get('canvas_image')
        compare_image_data = request.files.get('compare_image')
        
        if not canvas_image_data or not compare_image_data:
            return jsonify({"error": "No images provided"}), 400
        
        # Получаем данные пользователя из сессии
        user_data = session.get('user_data')
        if not user_data:
            return jsonify({"error": "User data not found in session"}), 400
        
        username = user_data.get('username')
        
        # Сохраняем изображения с новыми именами
        canvas_full_path = os.path.join('website/uploads', f"capture_{username}.jpg")
        restricted_full_path = os.path.join('website/uploads', f"capture_{username}_restricted.jpg")
        
        # Сохраняем изображения
        canvas_image_data.save(os.path.abspath(canvas_full_path))
        compare_image_data.save(os.path.abspath(restricted_full_path))

        # Загружаем и обрабатываем изображения с помощью face_recognition
        canvas_face_encoding = face_recognition.face_encodings(face_recognition.load_image_file(canvas_full_path))[0]
        restricted_face_encoding = face_recognition.face_encodings(face_recognition.load_image_file(restricted_full_path))[0]

        # Инициализируем пороговое значение
        threshold = 1.0
        while threshold >= 0:
            distance = face_recognition.face_distance([canvas_face_encoding], restricted_face_encoding)
            similarity_percentage = (1 - distance[0]) * 100  # Преобразование расстояния в процентное значение

            if similarity_percentage >= threshold * 100:
                return jsonify({"match": True, "similarity_percentage": similarity_percentage}), 200
            threshold -= 0.1

        return jsonify({"match": False, "similarity_percentage": 0}), 200

    finally:
        # В блоке finally удаляем файлы независимо от того, возникли ошибки или нет
        if os.path.exists(canvas_full_path):
            os.remove(canvas_full_path)
        if os.path.exists(restricted_full_path):
            os.remove(restricted_full_path)

@auth_profile.route('/compare', methods=['GET'])
def compare():
    filename = request.args.get('image', '')
    return render_template('try_compare.html', filename=filename)
