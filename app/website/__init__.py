from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from flask_bcrypt import Bcrypt


db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()

BASE_DIR = path.dirname(path.abspath(__file__))
DB_NAME = "database.db"
DB_PATH = path.join(BASE_DIR, DB_NAME)

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'niuoopkfpiowejo90123'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'

    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = 'auth_login.login' 

    from .views import views
    from .auth import auth_login, auth_signup, auth_profile, auth_compare

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth_login, url_prefix='/')
    app.register_blueprint(auth_signup, url_prefix='/')
    app.register_blueprint(auth_profile, url_prefix='/')
    app.register_blueprint(auth_compare, url_prefix='/')


    from .models import User, ProfileInfo

    with app.app_context():
        db.create_all()

    
    bcrypt.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))



    return app
