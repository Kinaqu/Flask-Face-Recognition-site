from flask import current_app
from website.models import User  # Подставьте вашу модель пользователя
import face_recognition
import numpy as np
from PIL import Image
import io

known_face_encodings = []
known_usernames = []

def initialize_face_recognition(app):
    with app.app_context():
        users = User.query.all()

        for user in users:
            try:
                # Преобразование данных изображения из blob в объект PIL Image
                face_image = Image.open(io.BytesIO(user.face_image))
                
                # Конвертация изображения в RGB формат
                face_image = face_image.convert("RGB")

                # Преобразование изображения в массив numpy
                face_encoding = np.array(face_image)

                # Получение кодировки лица
                face_encoding = face_recognition.face_encodings(face_encoding)[0]

                known_face_encodings.append(face_encoding)
                known_usernames.append(user.username)

            except Exception as e:
                print(f"Error processing face for user {user.username}: {e}")