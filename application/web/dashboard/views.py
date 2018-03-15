import dateutil.parser
from flask import request, redirect, url_for, flash, render_template
from flask_login import login_required
from pymongo import DESCENDING
from web import client
from web import q
from web import run_crawler
from web.config import *
from web.filters import *
from web.helper import extract_onions
from web.search.forms import SearchForm
from web.stats import onion_stats as oss
from werkzeug.utils import secure_filename
from time import sleep
from . import dashboardbp
from .forms import *


@dashboardbp.route('/', methods=['GET', 'POST'])
@login_required
def dashboard():
    search_form = SearchForm(request.form)
    range_stats_form = RangeStats()
    status_count = oss.get_requests_stats_all()
    multiple_urls_form = MultipleOnion()
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
            return render_template('dashboard.html', search_form=search_form,
                                   status_count=status_count, range_stats=range_stats_form,
                                   time_series=time_series,multiple_urls_form=multiple_urls_form,
                                   last_200=last_200, last_all=last_all)

    print ("DASHBOARD BEFORE FORM")
    if multiple_urls_form.validate_on_submit():
        seeds = []
        print ("FORM")
        if multiple_urls_form.seed_file.data:
            filename = secure_filename(multiple_urls_form.seed_file.data.filename)
            path_to_save = seed_upload_dir + filename
            multiple_urls_form.seed_file.data.save(path_to_save)
            _seed_file = open(path_to_save,'r')
            seed_file = extract_onions(_seed_file.read())
            _seed_file.close()
            for seed in seed_file:
                seeds.append(seed.strip())

        print (multiple_urls_form.urls.data)
        # print ("*"*100)
        if multiple_urls_form.urls.data:
            urls = extract_onions(multiple_urls_form.urls.data)
            for url in urls:
                seeds.append(url.strip())
        try:
            print (seeds)
            for seed in seeds:
                job = q.enqueue_call(
                    func=run_crawler, args=(seed,), ttl=0
                )
                # sleep(0.1) #delay between jobs
                # print (job.result)
            # if job.get_id():
            flash('New onions added to crawler queue ' ,'success')
            return render_template('dashboard.html', search_form=search_form,
                                   status_count=status_count, range_stats=range_stats_form,
                                   multiple_urls_form=multiple_urls_form,
                                   last_200=last_200, last_all=last_all)
        except Exception:
            # print(Exception)
            # print("ERROR")
            flash('Crawler service is down.','danger')

    print (multiple_urls_form.errors)



    return render_template('dashboard.html', search_form=search_form,
                           status_count=status_count, range_stats=range_stats_form,
                           multiple_urls_form=multiple_urls_form, last_200=last_200, last_all=last_all)



