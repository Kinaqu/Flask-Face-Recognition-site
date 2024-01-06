import json
from flask import Blueprint, redirect, url_for, session, request, render_template, flash
from . import db
from .models import User, ProfileInfo
import logging
from colorama import init, Fore
from typing import Dict, Any, Tuple, Optional, Union
from flask_login import login_required, logout_user, current_user

views = Blueprint('views', __name__)

@views.route('/',methods=['GET'])
def main():
    return render_template('main.html')    





@views.route('/about_us', methods=['GET'])
def about_us():
    return render_template('about_us.html')


@views.route('/contacts', methods=['GET'])
def contacts():
    return render_template('contacts.html')


@views.errorhandler(500)
def internal_server_error(e):
    try:
        log_message = f"{Fore.MAGENTA}Internal Server Error: {e}"
        print(log_message)
    except UnicodeEncodeError:
        pass
    return render_template('500.html'), 500


@views.errorhandler(404)
def page_not_found(e):
    try:
        print(f"Page Not Found: {e}")
    except UnicodeEncodeError:
        pass
    return render_template('404.html'), 404