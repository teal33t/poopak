from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, current_user
from web import captcha, client
from web.models import User

from web.search.forms import SearchForm
from . import authbp
from .forms import *


@authbp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if current_user.is_authenticated:
        redirect(url_for("dashboard.dashboard"))
    if captcha.validate():
        print ("TEST")
        if request.method == 'POST' and form.validate_on_submit():
            print("TEST1")
            user = client.crawler.users.find_one({"_id": form.username.data})
            if user and User.validate_login(user['password'], form.password.data):
                user_obj = User(user['_id'])
                login_user(user_obj)
                flash("Logged in successfully", 'success')
                return redirect(request.args.get("next") or url_for("dashboard.dashboard"))
            flash("Wrong username or password", 'danger')
    elif not captcha.validate():
        flash("Captcha is wrong!", 'danger')

    print (form.errors)
    search_form = SearchForm()
    return render_template('auth/login.html', title='login', form=form, search_form=search_form)

@authbp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


