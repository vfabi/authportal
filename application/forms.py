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

from flask_wtf import FlaskForm
from wtforms.fields import SubmitField, PasswordField, TextField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Email, Length, EqualTo


class LoginForm(FlaskForm):
    username = TextField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    captcha_text = TextField('Captcha', validators=[DataRequired()])
    submit = SubmitField('Submit')
