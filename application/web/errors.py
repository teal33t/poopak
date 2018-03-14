from flask_wtf.csrf import CSRFError
from . import app
from flask import render_template

from .search.forms import SearchForm

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    search_form = SearchForm()
    return render_template('error.html', title="Session expired", code="401", description="Form session expired.",
                           search_form=search_form)


@app.errorhandler(404)
def page_not_found(e):
    search_form = SearchForm()
    return render_template('error.html', title="PAGE NOT FOUND", code="404", description="Requested page not found.",
                           search_form=search_form)