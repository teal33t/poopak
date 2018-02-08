from flask_wtf.csrf import CSRFError

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    return render_template('error/error.html', title="Session expired", code="401", description="Form session expired.")


@app.errorhandler(404)
def page_not_found(e):
    return render_template('error/error.html', title="PAGE NOT FOUND", code="404", description="Requested page not found.")


