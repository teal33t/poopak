import base64
from random import SystemRandom
import logging

from captcha.image import ImageCaptcha
from flask import session, request, Markup
import string, random

class SessionCaptcha(object):
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.enabled = app.config.get("CAPTCHA_ENABLE", True)
        self.digits = app.config.get("CAPTCHA_LENGTH", 5)
        self.max = 10 ** self.digits
        self.image_generator = ImageCaptcha(width=200)
        self.rand = SystemRandom()

        def _generate():
            if not self.enabled:
                return ""
            base64_captcha = self.generate()
            return Markup("<img src='{}'>".format("data:image/png;base64, {}".format(base64_captcha)))

        app.jinja_env.globals['captcha'] = _generate

        session_type = app.config.get('SESSION_TYPE', None)

    def generate(self):
        """
        Generates and returns a numeric captcha image in base64 format.
        Saves the correct answer in `session['captcha_answer']`
        Use later as:
        src = captcha.generate()
        <img src="{{src}}">
        """
        answer = self.rand.randrange(self.max)
        answer = str(answer).zfill(self.digits)

        chars = "qwertyuiopasdfghjklzxcvbnm1234567890"
        for _ in answer:
            answer = answer.replace(_,random.choice(chars))

        image_data = self.image_generator.generate(answer)
        base64_captcha = base64.b64encode(image_data.getvalue()).decode("ascii")
        logging.debug('Generated captcha with answer: ' + answer)
        session['captcha_answer'] = answer
        return base64_captcha

    def validate(self, form_key="captcha", value=None):
        if not self.enabled:
            return True

        session_value = session.get('captcha_answer', None)
        if not session_value:
            return False

        if not value and form_key in request.form:
            value = request.form[form_key].strip()

        session['captcha_answer'] = None
        return value and value == session_value

    def get_answer(self):
        return session.get('captcha_answer', None)