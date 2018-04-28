from flask_wtf import FlaskForm
from wtforms import DateField, SubmitField, TextAreaField, BooleanField
from flask_wtf.file import FileField, FileRequired

class RangeStats(FlaskForm):
    from_dt = DateField('From Date', format="%m/%d/%Y")
    to_dt = DateField('To Date', format="%m/%d/%Y")
    submit = SubmitField("Get")


class MultipleOnion(FlaskForm):
    urls = TextAreaField("URLs")
    seed_file = FileField("Seed File")
    extract_emails = BooleanField("Extract emails")
    extract_btcaddr = BooleanField("Extract BTC addresses")
    extract_pub_pgp = BooleanField("Extract Pub PGP Key")
    submit = SubmitField("Run Crawler")


