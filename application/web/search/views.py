import datetime
import re

from bson.objectid import ObjectId
from flask import request, redirect, url_for, flash, render_template, Response
from pymongo import DESCENDING
from .. import captcha
from .. import client

from ..queues import crawler_q
from ..config import *
from ..filters import *

from .. import run_crawler
from .forms import SearchForm, AddOnionForm, ReportOnionForm

from ..paginate import Pagination
from . import searchbp

import time
from urllib.parse import urlparse, urlunparse

@searchbp.route('/', methods=['GET', 'POST'])
def index():
    # print (client.crawler.documents.find().count())
    search_form = SearchForm(request.form)
    if search_form.validate_on_submit():
        return redirect(url_for('.search', phrase=search_form.phrase.data.lower()))
    try:
        alive_onions = client.crawler.documents.find({"status": 200}).count()
        offline_checked_onions = client.crawler.documents.find({"status": 503}).count()
        last_crawled = client.crawler.documents.find().sort("seen_time", DESCENDING).limit(1)
        checked_onions = client.crawler.documents.find().count()
        return render_template('index.html', form=search_form,
                               checked_onions=checked_onions,
                               alive_onions=alive_onions,
                               offline_onions=offline_checked_onions,
                               last_crawled=last_crawled[0]['seen_time'])

    except:

        return render_template('index.html', form=search_form)


@searchbp.route('/search/<phrase>/', methods=["GET"])
@searchbp.route('/search/<phrase>/<int:page_number>', methods=["GET"])
def search(phrase, page_number=1):
    # report_form = ReportOnionForm()
    search_form = SearchForm()
    regex = " %s " % phrase
    try:
        all_count = client.crawler.documents.find({"body": re.compile(regex, re.IGNORECASE)}).count()
        pagination = Pagination(page_number, n_per_page, all_count)
        all = client.crawler.documents.find(
            {"body": re.compile(regex, re.IGNORECASE)}
        ).sort("seen_time", DESCENDING).skip(
            (page_number - 1) * n_per_page).limit(n_per_page)
    except:
        return render_template('result.html',phrase=phrase, all_count=0,
                               search_form=search_form)

    return render_template('result.html',
                           results=all,
                           pagination=pagination,
                           phrase=phrase, search_form=search_form,
                           all_count=all_count)

@searchbp.route('/report/<string:id>', methods=["GET", "POST"])
def report(id):
    report_form = ReportOnionForm()
    search_form = SearchForm()
    doc = None
    try:
        doc = client.crawler.documents.find_one({"_id": ObjectId(id)})
        report_form.url = doc['url']
        report_form.id = id
    except:
        flash("Invalid page")
        redirect(url_for('search.index'))

    if report_form.validate_on_submit():
        if captcha.validate():
            client.crawler.documents.update_one({'_id': ObjectId(id)},
                                                {
                                                    '$push': {
                                                        'tags':
                                                            {
                                                                "report_body": report_form.body.data,
                                                                "report_date": datetime.datetime.utcnow()
                                                            }
                                                    }})
            flash('Reported! your are helping community.' , 'success')
            redirect(url_for("search.index"))
        else:
            flash("Wrong captcha", 'danger')

    if doc['url']:
        return render_template('report.html', search_form=search_form, report_form=report_form)

        # doc = client.crawler.documents.update_one({'_id': id}, {"$set": {"reported": 1,}})


@searchbp.route('/new/', methods=['GET', 'POST'])
def add_onion():
    add_form = AddOnionForm()
    search_form = SearchForm()

    if add_form.validate_on_submit():
        if captcha.validate():
            url = add_form.url.data.strip()
            # try:
            #     exist = client.crawler.documents.find({"url": url}).count()
            # except:
            #     exist = 0
            #
            # if exist:
            #     flash('This onion is already indexed', 'warning')
            #     return redirect(url_for("search.add_onion"))

            print ("SEARCH BEFORE TRY")
            try:

                # print (url)
                parsed_url = urlparse(url)
                if parsed_url.scheme == None or parsed_url.scheme == "":
                    url = "http://%s" % url
                job = crawler_q.enqueue_call(
                    func=run_crawler, args=(url,), ttl=60, result_ttl=10
                )
                print (job)
                if job.get_id():
                    print (vars(job))
                    flash('New onion added to crawler queue.', 'success')

                return redirect(url_for("index"))
            except Exception:
                # print (Exception)
                print ("ERROR")
                # exit(0)
        else:
            flash("Captcha is not validate", 'danger')
            return redirect(url_for("search.add_onion"))
    elif "url" in add_form.errors:
        flash("Address is not valid, onion must be at least 16 chars, \
                ie. http://xxxxxxxxxxxxxxxx.onion or xxxxxxxxxxxxxxxx.onion", 'danger')
        return redirect(url_for("search.add_onion"))
    # print (add_form.errors)

    return render_template('new.html', add_form=add_form, search_form=search_form)



@searchbp.route('/directory/', methods=["GET"])
@searchbp.route('/directory/<int:page_number>', methods=["GET"])
def directory(page_number=1):
    search_form = SearchForm()
    try:
        all_count = client.crawler.documents.find({'status':200}).count()
        pagination = Pagination(page_number, n_per_page, all_count)
        all = client.crawler.documents.find({'status':200}).sort("seen_time", DESCENDING).skip(
            (page_number - 1) * n_per_page).limit(n_per_page)
    except:
        print ("ERROR[?]")
        return render_template('directory.html',
                               search_form=search_form,
                               all_count=0)

    return render_template('directory.html',
                           results=all,
                           pagination=pagination,
                           search_form=search_form,
                           all_count=all_count)


@searchbp.route('/directory/all', methods=["GET"])
@searchbp.route('/directory/all/<int:page_number>', methods=["GET"])
def directory_all(page_number=1):
    search_form = SearchForm()
    try:
        all_count = client.crawler.documents.find().count()
        pagination = Pagination(page_number, n_per_page, all_count)
        all = client.crawler.documents.find().sort("seen_time", DESCENDING).skip(
            (page_number - 1) * n_per_page).limit(n_per_page)
        is_all = True
    except:
        return render_template('directory.html',
                               search_form=search_form,
                               all_count=0)
    return render_template('directory.html',
                           results=all,
                           pagination=pagination,
                           search_form=search_form,
                           all_count=all_count, is_all=is_all)


@searchbp.route('/faq')
def faq():
    search_form = SearchForm()
    return render_template('faq.html', search_form = search_form)


@searchbp.route('/export_all')
def export_csv():
    all = client.crawler.documents.find({'status': 200})
    result = "# 200 OK status list\n "
    for item in all:
        result = str("%s%s\n" % (result, item['url']))
    return Response(result, mimetype='text/plain')
    # return render_template_string(result)
    # return render_template('faq.html', search_form = search_form)
