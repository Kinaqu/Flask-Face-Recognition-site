from . import db
from flask_login import UserMixin, login_required
from sqlalchemy.sql import func




class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String, nullable=True)
    face_image = db.Column(db.LargeBinary, nullable=True, unique=True)
    profile = db.relationship('ProfileInfo', back_populates='user')


    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

class ProfileInfo(db.Model):
    __tablename__ = 'profile_info'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    birth_date = db.Column(db.Date, nullable=True)
    position = db.Column(db.String(30), nullable=True)
    experience = db.Column(db.Integer, nullable=True)
    email = db.Column(db.String(150), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', back_populates='profile')



