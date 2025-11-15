"""
Forms for dashboard views.

This module defines WTForms for dashboard operations including
statistics range selection and multiple onion URL submission.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import BooleanField, DateField, SubmitField, TextAreaField, validators


class RangeStats(FlaskForm):
    """Form for selecting date range for statistics."""
    
    from_dt = DateField("From Date", format="%m/%d/%Y")
    to_dt = DateField("To Date", format="%m/%d/%Y")
    submit = SubmitField("Get")
    
    def validate(self, extra_validators=None):
        """
        Validate the form with custom logic.
        
        Ensures that from_dt is before to_dt if both are provided.
        """
        if not super().validate(extra_validators):
            return False
        
        if self.from_dt.data and self.to_dt.data:
            if self.from_dt.data > self.to_dt.data:
                self.to_dt.errors.append("End date must be after start date")
                return False
        
        return True


class MultipleOnion(FlaskForm):
    """Form for submitting multiple onion URLs for crawling."""
    
    urls = TextAreaField("URLs")
    seed_file = FileField("Seed File")
    extract_emails = BooleanField("Extract emails")
    extract_btcaddr = BooleanField("Extract BTC addresses")
    extract_pub_pgp = BooleanField("Extract Pub PGP Key")
    submit = SubmitField("Run Crawler")
    
    def validate(self, extra_validators=None):
        """
        Validate the form with custom logic.
        
        Ensures that either URLs or seed file is provided.
        """
        if not super().validate(extra_validators):
            return False
        
        # At least one of urls or seed_file must be provided
        has_urls = self.urls.data and self.urls.data.strip()
        has_file = self.seed_file.data
        
        if not has_urls and not has_file:
            self.urls.errors.append("Please provide URLs or upload a seed file")
            return False
        
        return True
