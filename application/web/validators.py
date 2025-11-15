"""
Custom form validators for the web application.

This module provides reusable validators for WTForms that can be used
across different forms in the application.
"""

from wtforms import ValidationError

from application.utils.url_utils import is_valid_onion_url, normalize_url


def validate_onion_url(form, field):
    """
    Validate that the field contains a valid onion URL.
    
    This validator checks if the URL is a properly formatted onion address
    with minimum required length (16 characters for the onion address part).
    
    Args:
        form: The form instance
        field: The field being validated
        
    Raises:
        ValidationError: If the URL is not a valid onion address
        
    Example:
        class MyForm(FlaskForm):
            url = StringField('URL', validators=[validate_onion_url])
    """
    if not field.data:
        return
    
    url = field.data.strip()
    
    # Normalize URL (add scheme if missing)
    url = normalize_url(url)
    
    # Validate onion URL format
    if not is_valid_onion_url(url):
        raise ValidationError(
            "Address is not valid, onion must be at least 16 chars, "
            "ie. http://xxxxxxxxxxxxxxxx.onion or xxxxxxxxxxxxxxxx.onion"
        )


def validate_min_length(min_length: int):
    """
    Create a validator that checks minimum string length.
    
    Args:
        min_length: Minimum required length
        
    Returns:
        Validator function
        
    Example:
        class MyForm(FlaskForm):
            field = StringField('Field', validators=[validate_min_length(10)])
    """
    def _validate(form, field):
        if field.data and len(field.data.strip()) < min_length:
            raise ValidationError(
                f"Field must be at least {min_length} characters long"
            )
    
    return _validate


def validate_not_empty(form, field):
    """
    Validate that the field is not empty or whitespace only.
    
    Args:
        form: The form instance
        field: The field being validated
        
    Raises:
        ValidationError: If the field is empty or contains only whitespace
    """
    if not field.data or not field.data.strip():
        raise ValidationError("This field cannot be empty")


def validate_document_id(form, field):
    """
    Validate that the field contains a valid MongoDB ObjectId format.
    
    MongoDB ObjectIds are 24-character hexadecimal strings.
    
    Args:
        form: The form instance
        field: The field being validated
        
    Raises:
        ValidationError: If the document ID format is invalid
    """
    if not field.data:
        return
    
    document_id = field.data.strip()
    
    # Check length
    if len(document_id) != 24:
        raise ValidationError("Invalid document ID format")
    
    # Check if hexadecimal
    try:
        int(document_id, 16)
    except ValueError:
        raise ValidationError("Invalid document ID format")
