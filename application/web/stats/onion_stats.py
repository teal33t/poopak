from .. import client


def get_all_unique_page():
    count = client.crawler.documents.distinct('url')
    return count
#
# def get_requests_stats_series(from_date, to_date):
#     # printto_date - from_date
#
#     import datetime
#     delta_time = days_hours_minutes(to_date-from_date)
#     # if delta_time[0] > 1:
#     #     pipelines = []
#     #     ctl_date = to_date - datetime.timedelta(days=7)
#     #     if ctl_date - from_date > 0:
#     #         # for days in range()
#     #     pipelines.append(
#     #         [
#     #             {
#     #                 "$match": {
#     #                     "seen_time": {"$gt": from_date, "$lte": to_date}
#     #                 },
#     #             },
#     #             {"$unwind": "$status"},
#     #             {"$group": {"_id": "$status", "count": {"$sum": 1}}},
#     #         ]
#     #     )
#
#
#     pipeline = [
#         {
#             "$match": {
#                 "seen_time": { "$gt": from_date, "$lte": to_date }
#             },
#         },
#         {"$unwind": "$status"},
#         {"$group": {"_id": "$status", "count": {"$sum": 1}}},
#     ]
#
#     counts = client.crawler.documents.aggregate(pipeline)
#
#     result = []
#     for id in counts:
#         result.append({'type':id['_id'], 'count': id['count']})
#     return result
#


def get_requests_stats(from_date, to_date):
    pipeline = [
        {
            "$match": {
                "seen_time": { "$gte": from_date, "$lte": to_date }
            },
        },
        {"$unwind": "$status"},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
    ]
    print (from_date)
    print (to_date)
    counts = client.crawler.documents.aggregate(pipeline)
    # print (list(counts))
    result = []
    for id in counts:
        result.append({'type':id['_id'], 'count': id['count']})

    print (result)
    return result


# {"503": 1230, ... }
def get_requests_stats_all():
    pipeline = [
        {"$unwind": "$status"},
        {"$group": {"_id": "$status", "count":{"$sum": 1}}},
    ]
    counts = client.crawler.documents.aggregate(pipeline)

    # counts = client.crawler.documents.aggregate(pipeline)
    #
    # label = []
    # count = []
    # for id in counts:
    #     label.append(id['_id'])
    #     count.append(id['count'])


    result = []
    for id in counts:
        result.append({'type':id['_id'], 'count': id['count']})

    # print (result)
    return result
