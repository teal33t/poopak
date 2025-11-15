"""
Forms for search-related views.

This module defines WTForms for search, adding onions, and reporting.
"""

from flask_wtf import FlaskForm
from wtforms import HiddenField, StringField, SubmitField, TextAreaField, validators

from application.web.validators import validate_onion_url


class SearchForm(FlaskForm):
    """Form for searching documents."""
    
    phrase = StringField("Phrase", [validators.DataRequired()])
    submit = SubmitField("Go")


class AddOnionForm(FlaskForm):
    """Form for adding a new onion URL to the crawler queue."""
    
    url = StringField(
        "Onion Url",
        [validators.DataRequired(), validators.Length(min=16), validate_onion_url]
    )
    captcha = StringField("captcha", validators=[validators.DataRequired()])
    submit = SubmitField("+ add and scan service")


class ReportOnionForm(FlaskForm):
    """Form for reporting a document."""
    
    id = HiddenField()
    url = HiddenField()
    captcha = StringField("captcha", validators=[validators.DataRequired()])
    body = TextAreaField("Description")
    submit = SubmitField("report")
