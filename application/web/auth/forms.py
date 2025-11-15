from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, validators
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):

    username = StringField("Username", validators=[validators.DataRequired()])
    password = PasswordField("Password", validators=[validators.DataRequired()])
    captcha = StringField("captcha", validators=[validators.DataRequired()])
    submit = SubmitField("Login")
