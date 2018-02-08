# FORMS
from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, HiddenField, validators, TextAreaField


class SearchForm(FlaskForm):
    phrase = StringField('Phrase', [validators.required()])
    submit = SubmitField('Go')

class AddOnionForm(FlaskForm):
    url = StringField("Onion Url", [validators.required(), validators.Length(min=16)])
    captcha = StringField('captcha', validators=[validators.required()])
    submit = SubmitField('+ add and scan service')


class ReportOnionForm(FlaskForm):
    id = HiddenField()
    url = HiddenField()
    captcha = StringField('captcha', validators=[validators.required()])
    body = TextAreaField("Description")
    submit = SubmitField("report")

