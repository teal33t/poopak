import logging
from typing import Union

from flask import Response, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from application.services.authentication_service import AuthenticationService
from application.utils.exceptions import DatabaseConnectionError
from application.web.captchar import SessionCaptcha
from application.web.decorators import inject_services

from ..search.forms import SearchForm
from . import authbp
from .forms import LoginForm

logger = logging.getLogger(__name__)


@authbp.route("/login", methods=["GET", "POST"])
@inject_services("authentication_service", "captcha")
def login(authentication_service: AuthenticationService = None, captcha: SessionCaptcha = None) -> Union[str, Response]:
    """
    Handle user login with captcha validation.

    Args:
        authentication_service: Injected AuthenticationService instance
        captcha: Injected SessionCaptcha instance

    Returns:
        Rendered login template or redirect to dashboard
    """
    form = LoginForm()
    search_form = SearchForm()

    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST" and form.validate_on_submit():
        # Validate captcha with improved error messages
        is_valid, error_message = captcha.validate()
        
        if not is_valid:
            if error_message:
                flash(error_message, "danger")
            return render_template("auth/login.html", title="login", form=form, search_form=search_form)
        
        try:
            user_obj = authentication_service.authenticate_user(
                form.username.data,
                form.password.data
            )

            if user_obj:
                login_user(user_obj)
                flash("Logged in successfully", "success")
                return redirect(request.args.get("next") or url_for("dashboard.dashboard"))
            else:
                flash("Wrong username or password", "danger")

        except DatabaseConnectionError as e:
            logger.error(f"Database error during login: {str(e)}")
            flash("Error connecting to database", "error")

        except Exception as e:
            logger.error(f"Unexpected error during login: {str(e)}")
            flash("An unexpected error occurred", "error")

    if form.errors:
        logger.debug(f"Login form validation errors: {form.errors}")

    return render_template("auth/login.html", title="login", form=form, search_form=search_form)


@authbp.route("/logout")
def logout() -> Response:
    """
    Handle user logout.

    Returns:
        Redirect to login page
    """
    try:
        username = current_user.get_id() if current_user.is_authenticated else "unknown"
        logout_user()
        logger.info(f"User {username} logged out")
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")

    return redirect(url_for("auth.login"))
