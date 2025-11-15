import logging
from datetime import datetime
from typing import Any, Dict, List

from flask import current_app

from application.utils.exceptions import DatabaseConnectionError

logger = logging.getLogger(__name__)


def get_all_unique_page() -> List[str]:
    """
    Get all unique page URLs from the database.

    Returns:
        List of unique URLs
    """
    try:
        document_repository = current_app.document_repository
        count = document_repository.collection.distinct("url")
        logger.info(f"Retrieved {len(count)} unique pages")
        return count
    except DatabaseConnectionError as e:
        logger.error(f"Database error retrieving unique pages: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error retrieving unique pages: {str(e)}")
        return []


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


def get_requests_stats(from_date: datetime, to_date: datetime) -> List[Dict[str, Any]]:
    """
    Get request statistics grouped by status code for a date range.

    Args:
        from_date: Start date for the range
        to_date: End date for the range

    Returns:
        List of dictionaries with 'type' (status code) and 'count' keys
    """
    try:
        document_repository = current_app.document_repository
        pipeline = [
            {
                "$match": {"seen_time": {"$gte": from_date, "$lte": to_date}},
            },
            {"$unwind": "$status"},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        ]

        logger.info(f"Getting request stats from {from_date} to {to_date}")
        counts = document_repository.collection.aggregate(pipeline)

        result = []
        for id in counts:
            result.append({"type": id["_id"], "count": id["count"]})

        logger.info(f"Retrieved {len(result)} status groups for date range")
        return result

    except DatabaseConnectionError as e:
        logger.error(f"Database error retrieving request stats: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error retrieving request stats: {str(e)}")
        return []


def get_requests_stats_all() -> List[Dict[str, Any]]:
    """
    Get request statistics grouped by status code for all documents.

    Returns:
        List of dictionaries with 'type' (status code) and 'count' keys
        Example: [{"type": 200, "count": 1230}, {"type": 503, "count": 45}]
    """
    try:
        document_repository = current_app.document_repository
        pipeline = [
            {"$unwind": "$status"},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        ]

        logger.info("Getting all request stats")
        counts = document_repository.collection.aggregate(pipeline)

        result = []
        for id in counts:
            result.append({"type": id["_id"], "count": id["count"]})

        logger.info(f"Retrieved {len(result)} status groups")
        return result

    except DatabaseConnectionError as e:
        logger.error(f"Database error retrieving all request stats: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error retrieving all request stats: {str(e)}")
        return []
