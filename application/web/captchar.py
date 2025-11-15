"""
Captcha module for session-based captcha generation and validation.

This module provides the SessionCaptcha class for generating and validating
captcha images to prevent automated form submissions.
"""

import base64
import logging
import random
from functools import wraps
from random import SystemRandom
from typing import Callable, Optional, Tuple

from captcha.image import ImageCaptcha
from flask import Flask, flash, request, session
from markupsafe import Markup

from application.config.constants import (
    CAPTCHA_CHAR_POOL,
    CAPTCHA_DEFAULT_LENGTH,
    CAPTCHA_ERROR_EXPIRED,
    CAPTCHA_ERROR_INVALID,
    CAPTCHA_ERROR_MISSING,
    CAPTCHA_FORM_KEY,
    CAPTCHA_IMAGE_WIDTH,
    CAPTCHA_SESSION_KEY,
)

logger = logging.getLogger(__name__)


class SessionCaptcha:
    """
    Session-based captcha generator and validator.

    This class generates captcha images and stores the answer in the user's session.
    It provides methods for generating captcha images and validating user input.

    Attributes:
        enabled: Whether captcha validation is enabled
        digits: Number of digits in the captcha
        max: Maximum value for random number generation
        image_generator: ImageCaptcha instance for generating images
        rand: SystemRandom instance for secure random number generation
    """

    def __init__(self, app: Optional[Flask] = None) -> None:
        """
        Initialize the SessionCaptcha instance.

        Args:
            app: Optional Flask application instance to initialize with
        """
        self.enabled: bool = True
        self.digits: int = CAPTCHA_DEFAULT_LENGTH
        self.max: int = 10**self.digits
        self.image_generator: Optional[ImageCaptcha] = None
        self.rand: SystemRandom = SystemRandom()

        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """
        Initialize the captcha with a Flask application.

        Args:
            app: Flask application instance
        """
        self.enabled = app.config.get("CAPTCHA_ENABLE", True)
        self.digits = app.config.get("CAPTCHA_LENGTH", CAPTCHA_DEFAULT_LENGTH)
        self.max = 10**self.digits
        self.image_generator = ImageCaptcha(width=CAPTCHA_IMAGE_WIDTH)
        self.rand = SystemRandom()

        def _generate() -> str:
            """Generate captcha HTML for Jinja templates."""
            if not self.enabled:
                return ""
            base64_captcha = self.generate()
            return Markup(
                "<img src='{}'>".format(
                    "data:image/png;base64, {}".format(base64_captcha)
                )
            )

        app.jinja_env.globals["captcha"] = _generate

    def generate(self) -> str:
        """
        Generate a captcha image and store the answer in the session.

        Returns:
            Base64-encoded captcha image string

        Raises:
            RuntimeError: If image_generator is not initialized
        """
        if self.image_generator is None:
            raise RuntimeError("SessionCaptcha not initialized with Flask app")

        # Generate random number and convert to string with leading zeros
        answer = self.rand.randrange(self.max)
        answer_str = str(answer).zfill(self.digits)

        # Replace each digit with a random character from the pool
        obfuscated_answer = answer_str
        for digit in answer_str:
            obfuscated_answer = obfuscated_answer.replace(
                digit, random.choice(CAPTCHA_CHAR_POOL), 1
            )

        # Generate image and encode to base64
        image_data = self.image_generator.generate(obfuscated_answer)
        base64_captcha = base64.b64encode(image_data.getvalue()).decode("ascii")

        logger.debug(f"Generated captcha with answer: {obfuscated_answer}")
        session[CAPTCHA_SESSION_KEY] = obfuscated_answer

        return base64_captcha

    def validate(
        self, form_key: str = CAPTCHA_FORM_KEY, value: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate captcha input against the session value.

        Args:
            form_key: Form field name containing the captcha input
            value: Optional captcha value to validate (if not provided, reads from form)

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if captcha is valid, False otherwise
            - error_message: Error message if validation failed, None if successful
        """
        if not self.enabled:
            return True, None

        session_value = session.get(CAPTCHA_SESSION_KEY, None)

        # Clear the session value to prevent reuse
        session[CAPTCHA_SESSION_KEY] = None

        if not session_value:
            return False, CAPTCHA_ERROR_EXPIRED

        # Get value from form if not provided
        if not value and form_key in request.form:
            value = request.form[form_key].strip()

        if not value:
            return False, CAPTCHA_ERROR_MISSING

        if value != session_value:
            return False, CAPTCHA_ERROR_INVALID

        return True, None

    def validate_simple(
        self, form_key: str = CAPTCHA_FORM_KEY, value: Optional[str] = None
    ) -> bool:
        """
        Simple boolean validation without error message.

        Args:
            form_key: Form field name containing the captcha input
            value: Optional captcha value to validate

        Returns:
            True if captcha is valid, False otherwise
        """
        is_valid, _ = self.validate(form_key, value)
        return is_valid

    def get_answer(self) -> Optional[str]:
        """
        Get the current captcha answer from the session.

        Returns:
            The captcha answer string if it exists, None otherwise
        """
        return session.get(CAPTCHA_SESSION_KEY, None)


def require_captcha(
    form_key: str = CAPTCHA_FORM_KEY, flash_errors: bool = True
) -> Callable:
    """
    Decorator to require captcha validation for a view function.

    This decorator validates the captcha before executing the view function.
    If validation fails, it flashes an error message and returns None, allowing
    the view to handle the failure appropriately.

    Args:
        form_key: Form field name containing the captcha input
        flash_errors: Whether to flash error messages on validation failure

    Returns:
        Decorated function

    Example:
        @app.route('/submit', methods=['POST'])
        @require_captcha()
        def submit_form():
            if not captcha_valid:
                return render_template('form.html')
            # Process form...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            from flask import current_app

            captcha = current_app.extensions.get("captcha")
            if captcha is None:
                logger.warning("Captcha not initialized in application")
                return func(*args, **kwargs)

            is_valid, error_message = captcha.validate(form_key)

            if not is_valid and error_message:
                if flash_errors:
                    flash(error_message, "error")
                logger.debug(f"Captcha validation failed: {error_message}")

            # Set a flag in kwargs so the view can check validation status
            kwargs["captcha_valid"] = is_valid

            return func(*args, **kwargs)

        return wrapper

    return decorator
