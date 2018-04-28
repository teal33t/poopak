import dateutil.parser
from flask import request, redirect, url_for, flash, render_template
from flask_login import login_required
from pymongo import DESCENDING
from web import client
# from web import q
from web import run_crawler


from web.config import *
from web.filters import *
from web.helper import extract_onions
from web.search.forms import SearchForm
from web.stats import onion_stats as oss
from web.paginate import Pagination
from web.scanner import subjects

from web.queues import detector_q, crawler_q

from werkzeug.utils import secure_filename
from . import dashboardbp
from .forms import *

from bson import ObjectId


@dashboardbp.route('/hs/<id>', methods=["GET"])
def hs_view(id=1):
    search_form = SearchForm()
    try:
        child_data = []
        result = client.crawler.documents.find_one({"_id":ObjectId(id)})
        if result['links']:
            for item in result['links']:
                child_data.append(client.crawler.documents.find_one({"url":item['url']}))
    except:
        print ("ERROR")
    return render_template('dashboard/hs.html',
                           item=result,
                           child_data=child_data,
                           search_form=search_form)


@dashboardbp.route('/hs_directory/', methods=["GET"])
@dashboardbp.route('/hs_directory/<int:page_number>', methods=["GET"])
def hs_directory(page_number=1):
    search_form = SearchForm()
    try:
        all_count = client.crawler.documents.find({'status':200}).count()
        pagination = Pagination(page_number, n_per_page, all_count)
        all = client.crawler.documents.find({ "$and":[{'status':200}, {"in_scope": {"$eq": False}}]}).sort("seen_time", DESCENDING).skip(
            (page_number - 1) * n_per_page).limit(n_per_page)
    except:
        print ("ERROR")
        return render_template('dashboard/hs_directory.html',
                               search_form=search_form,
                               all_count=0)

    return render_template('dashboard/hs_directory.html',
                           results=all,
                           pagination=pagination,
                           search_form=search_form,
                           all_count=all_count)



@dashboardbp.route('/hs/detect/<id>', methods=['GET', 'POST'])
@login_required
def detect_subjects(id):
    # if (id):
    detector_q.enqueue_call(subjects._text_subject, args=(id,), ttl=86400, result_ttl=1)

    flash("Detecting started.", "success")
    # q.enqueue_call(get_text_subject, args=(id,), ttl=86400, result_ttl=1)
    return redirect(url_for('dashboard.hs_view', id=id))
    # else:
    #     flash("Detector server is down.", "danger")
        # q.enqueue_call(get_text_subject, args=(id,), ttl=86400, result_ttl=1)
        # return redirect(url_for('dashboard.hs_view', id=id))


@dashboardbp.route('/statistics', methods=['GET', 'POST'])
@login_required
def statistics():
    pass


@dashboardbp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    pass

@dashboardbp.route('/upload_seed', methods=['GET', 'POST'])
@login_required
def upload_seed():
    search_form = SearchForm(request.form)
    multiple_urls_form = MultipleOnion()
    if multiple_urls_form.validate_on_submit():
        seeds = []
        print("FORM")
        if multiple_urls_form.seed_file.data:
            filename = secure_filename(multiple_urls_form.seed_file.data.filename)
            path_to_save = seed_upload_dir + filename
            multiple_urls_form.seed_file.data.save(path_to_save)

            _seed_file = open(path_to_save, 'r')
            seed_file = extract_onions(_seed_file.read())
            _seed_file.close()

            for seed in seed_file:
                seeds.append(seed.strip())

        # print (multiple_urls_form.urls.data)
        # print ("*"*100)
        if multiple_urls_form.urls.data:
            urls = extract_onions(multiple_urls_form.urls.data)
            for url in urls:
                seeds.append(url.strip())

        for seed in seeds:
            print(seed)
            crawler_q.enqueue_call(func=run_crawler, args=(seed,), ttl=86400, result_ttl=1)
            # sleep(0.1) #delay between jobs
            # print (job.result)

        flash('New onions added to crawler queue ', 'success')
        return render_template('dashboard/upload_seed.html', search_form=search_form,
                               multiple_urls_form=multiple_urls_form)

    return render_template('dashboard/upload_seed.html', search_form=search_form,
                           multiple_urls_form=multiple_urls_form)


    print (multiple_urls_form.errors)


@dashboardbp.route('/', methods=['GET', 'POST'])
@login_required
def dashboard():
    search_form = SearchForm(request.form)
    range_stats_form = RangeStats()
    status_count = oss.get_requests_stats_all()
    # print ("*"*1000)
    last_200 = 0
    last_all = 0

    try:
        last_200 = client.crawler.documents.find({"status": 200}).sort("seen_time", DESCENDING).limit(20)
        last_all = client.crawler.documents.find().sort("seen_time", DESCENDING).limit(20)
    except:
        print ("ERROR")

        # return render_template('dashboard.html', search_form=search_form,
        #                        range_stats=range_stats_form, multiple_urls_form=multiple_urls_form)

    # print(list(last_200))
    # print(list(last_all))

    if search_form.validate_on_submit():
        return redirect(url_for('.search', phrase=search_form.phrase.data.lower()))

    if range_stats_form.validate_on_submit():
        if range_stats_form.from_dt.data and range_stats_form.to_dt.data:
            time_series = oss.get_requests_stats(
                dateutil.parser.parse(str(range_stats_form.from_dt.data)),
                dateutil.parser.parse(str(range_stats_form.to_dt.data))
            )
            return render_template('dashboard/dashboard.html', search_form=search_form,
                                   status_count=status_count, range_stats=range_stats_form,
                                   time_series=time_series,multiple_urls_form=multiple_urls_form,
                                   last_200=last_200, last_all=last_all)





    return render_template('dashboard/dashboard.html', search_form=search_form,
                           status_count=status_count, range_stats=range_stats_form,
                            last_200=last_200, last_all=last_all)



