#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
    @project: authportal
    @component: core
    @copyright: © 2020 by vfabi
    @author: vfabi
    @support: vfabi
    @initial date: 2020-05-23 11:11:23
    @license: this file is subject to the terms and conditions defined
        in file 'LICENSE', which is part of this source code package
    @description:
    @todo:
"""

import os
import logging
from flask import Flask, session, request, flash, url_for, redirect, render_template, abort, g
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from application.forms import LoginForm
from application.utils import variables, logging_level, CustomCaptcha
from application.models import User


logging.basicConfig(level=logging_level, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")

captcha = CustomCaptcha(config={'SECRET_CSRF_KEY': variables['FLASK_SIMPLE_CAPTCHA_SECRET_CSRF_KEY']})
app = Flask(__name__, template_folder=os.path.abspath('application/templates'), static_folder='application/static')
app.config['SECRET_KEY'] = variables['flask_secret_key']
app = captcha.init_app(app)
app.jinja_env.globals.update(variables=variables)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = None
login_manager.login_message_category = 'success'


@login_manager.unauthorized_handler
def unauthorized():
    if variables['unauthorized_action'] == 'return_401':
        return '401', 401
    else:
        return redirect(url_for('login'))


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
@login_required
def index(path):
    code = 200
    msg = ''
    headers = [('x-auth', 'authenticated')]
    return msg, code, headers


@app.route('/auth',methods=['GET','POST'])
def login():
    form = LoginForm()

    if request.method == 'GET':
        return render_template('login.html', form=form, variables=variables, captcha=captcha.create())

    if form.validate_on_submit():
        username = request.form.get('username')
        password = request.form.get('password')
        captcha_hash = request.form.get('captcha-hash')
        captcha_text = request.form.get('captcha_text')
        redirect_url = request.args.get(variables['redirect_url_param_name'], default='/')
        if not captcha.verify(captcha_text, captcha_hash):
            flash('Captcha is not valid.', 'error')
            return redirect(f'{url_for("login")}?{variables["redirect_url_param_name"]}={redirect_url}')
        user = User.get(username=username, password=password)
        if user:
            if login_user(user):
                return redirect(redirect_url)
        flash('Username or password is invalid.', 'error')
        return redirect(f'{url_for("login")}?{variables["redirect_url_param_name"]}={redirect_url}')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@login_manager.user_loader
def load_user(id):
    return User.check(id=id)


@app.before_request
def before_request():
    g.user = current_user


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=8000,
        debug=False
    )
