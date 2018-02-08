import datetime
import re

from bson.objectid import ObjectId
from flask import request, redirect, url_for, flash, render_template
from pymongo import DESCENDING
from web import captcha
from web import client
from web import q
from web import run_crawler
from web.config import *
from web.filters import *
from .forms import SearchForm, AddOnionForm, ReportOnionForm

from web.paginate import Pagination
from . import searchbp


@searchbp.route('/', methods=['GET', 'POST'])
def index():
    # print (client.crawler.documents.find().count())
    search_form = SearchForm(request.form)
    if search_form.validate_on_submit():
        return redirect(url_for('.search', phrase=search_form.phrase.data.lower()))
    try:
        alive_onions = client.crawler.documents.find({"status": 200}).count()
        offline_checked_onions = client.crawler.documents.find({"status": 503}).count()
        last_crawled = client.crawler.documents.sort("seen_time", DESCENDING).limit(1)
        checked_onions = client.crawler.documents.count()
    except:

        return render_template('index.html', form=search_form)

    return render_template('index.html', form=search_form,
                           checked_onions=checked_onions,
                           alive_onions=alive_onions,
                           offline_onions=offline_checked_onions,
                           last_crawled=last_crawled[0]['seen_time'])

@searchbp.route('/search/<phrase>/', methods=["GET"])
@searchbp.route('/search/<phrase>/<int:page_number>', methods=["GET"])
def search(phrase, page_number=1):
    # report_form = ReportOnionForm()
    search_form = SearchForm()
    regex = " %s " % phrase
    try:
        all_count = client.crawler.documents.find({"body": re.compile(regex, re.IGNORECASE)}).count()
        pagination = Pagination(page_number, n_per_page, all_count)
        all = client.crawler.documents.find({"body": re.compile(regex, re.IGNORECASE)}).sort("seen_time", DESCENDING).skip(
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
    doc = client.crawler.documents.find_one({"_id": ObjectId(id)})
    report_form.url = doc['url']
    report_form.id = id
    if report_form.validate_on_submit():
        if captcha.validate():
            try:
                print (id)
                print(report_form.body.data)
                client.crawler.documents.update_one({'_id': ObjectId(id)},
                                                    {'$set': {"report": report_form.body.data,
                                                              "report_date": datetime.datetime.utcnow()}})
                flash('Reported! your are helping community.' , 'success')
                redirect(url_for("index"))
            except:
                flash("Error, please try later", 'danger')
                redirect(url_for("search.report", id=id))
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
            try:
                exist = client.crawler.documents.find({"url": url}).count()
            except:
                exist = 0

            if exist:
                flash('This onion is already indexed', 'warning')
                return redirect(url_for("search.add_onion"))

            try:
                print (url)
                job = q.enqueue_call(
                    func=run_crawler, args=(url,), timeout=500
                )
                print (job)
                if job.get_id():
                    flash('New onion added to crawler queue.', 'success')
                return redirect(url_for("index"))

            except Exception:
                print (Exception)
                print ("ERROR")
                # exit(0)
        else:
            flash("Captcha is not validate", 'danger')
            return redirect(url_for("search.add_onion"))
    elif "url" in add_form.errors:
        flash("Address is not valid, onion must be at least 16 chars, \
                ie. http://xxxxxxxxxxxxxxxx.onion or xxxxxxxxxxxxxxxx.onion", 'danger')
        return redirect(url_for("search.add_onion"))
    print (add_form.errors)

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
