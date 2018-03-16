from . import app

from pytz import timezone

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%d-%m-%Y - %H:%M:%S'):
    if value:
        value = value.replace(tzinfo=timezone('UTC'))
        return value.strftime(format)

@app.template_filter('limitbody')
def limitbody(value, size=700):
    if value:
        body = value.strip()
        return ("%s..." % body[:size] )


# @app.template_filter('http_rpr')
# def http_rpr(code):
#     if int(code) == 200:
#         return "<i class='glyphicon glyphicon-ok'></i>"