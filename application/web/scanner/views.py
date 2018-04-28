import dateutil.parser
from flask import request, redirect, url_for, flash, render_template
from flask_login import login_required
# from web import client
# from web import q
# from bson.objectid import ObjectId

from . import scannerbp

@scannerbp.route('/scanner', methods=['GET', 'POST'])
@login_required
def scanner_overview():
    pass
    # hidden_service = client.crawler.documents.find({'_id': ObjectId(id)})
    # return hidden_service