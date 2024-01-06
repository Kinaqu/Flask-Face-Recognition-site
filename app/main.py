from website import create_app
from website.face_recognition import initialize_face_recognition

app = create_app()
initialize_face_recognition(app)

if __name__ == '__main__':
        app.run(debug=True)
        