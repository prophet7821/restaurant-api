# Description: This file contains the code for generating the report for the uptime and downtime of the stores.
#The generate report function in this file can only handle smaller amounts of data. It is not scalable.

import datetime as dt
import pytz
from typing import Dict
from models import StoreStatus, StoreHours, StoreTimezone, db
from sqlalchemy import func
from concurrent.futures import ThreadPoolExecutor


# This function converts the local time to UTC time

def local_to_utc(local_dt, tz_str):
    tz = pytz.timezone(tz_str)
    local_dt = tz.localize(local_dt)
    return local_dt.astimezone(pytz.utc)


def utc_to_local(utc_dt, tz_str):
    tz = pytz.timezone(tz_str)
    utc_dt = utc_dt.replace(tzinfo=pytz.utc)
    return utc_dt.astimezone(tz)


def business_hours_start_end(day, start_time_local, end_time_local, tz_str):
    local_start = dt.datetime.combine(day, start_time_local)
    local_end = dt.datetime.combine(day, end_time_local)
    return local_to_utc(local_start, tz_str), local_to_utc(local_end, tz_str)


def count_uptime_downtime(store_statuses, start, end):
    uptime = 0
    downtime = 0
    prev_status = None
    prev_time = start

    for status in store_statuses:
        if prev_status is not None:
            duration = (status.timestamp_utc - prev_time).total_seconds() / 60
            if prev_status == 'active':
                uptime += duration
            else:
                downtime += duration

        prev_status = status.status
        prev_time = status.timestamp_utc

    return uptime, downtime


def get_store_statuses(store_id, start, end, page_size=1000):
    store_statuses = []
    offset = 0
    while True:
        batch = StoreStatus.query.filter(
            StoreStatus.store_id == store_id,
            func.cast(StoreStatus.timestamp_utc,
                      db.TIMESTAMP(timezone=True)) >= start,
            func.cast(StoreStatus.timestamp_utc,
                      db.TIMESTAMP(timezone=True)) <= end
        ).order_by(StoreStatus.timestamp_utc).limit(page_size).offset(offset).all()

        if not batch:
            break

        store_statuses.extend(batch)
        offset += page_size

    return store_statuses


def generate_report() -> Dict[int, Dict[str, float]]:
    report = {}
    stores = StoreStatus.query.all()

    for store in stores:
        store_timezone = StoreTimezone.query.filter_by(
            store_id=store.store_id).first()
        store_hours = StoreHours.query.filter_by(
            store_id=store.store_id).first()

        tz_str = store_timezone.timezone_str if store_timezone else 'America/Chicago'
        current_day = dt.datetime.now().date()
        last_week = current_day - dt.timedelta(days=7)

        for day in (last_week + dt.timedelta(days=n) for n in range(8)):

            start_time_local = dt.datetime.strptime(
                store_hours.start_time_local, "%H:%M:%S").time() if store_hours else dt.time(0, 0, 0)
            end_time_local = dt.datetime.strptime(
                store_hours.end_time_local, "%H:%M:%S").time() if store_hours else dt.time(23, 59, 59)

            start, end = business_hours_start_end(
                day, start_time_local, end_time_local, tz_str)

            store_statuses = get_store_statuses(store.store_id, start, end)

            if store_statuses:
                uptime, downtime = count_uptime_downtime(
                    store_statuses, start, end)

                if store.store_id not in report:
                    report[store.store_id] = {'uptime_last_hour': 0, 'uptime_last_day': 0, 'uptime_last_week': 0,
                                              'downtime_last_hour': 0, 'downtime_last_day': 0, 'downtime_last_week': 0}

                report[store.store_id]['uptime_last_hour'] += min(uptime, 60)
                report[store.store_id]['uptime_last_day'] += min(
                    uptime, 60 * 24)
                report[store.store_id]['uptime_last_week'] += uptime

                report[store.store_id]['downtime_last_hour'] += min(
                    downtime, 60)
                report[store.store_id]['downtime_last_day'] += min(
                    downtime, 60 * 24)
                report[store.store_id]['downtime_last_week'] += downtime
    return report


def generate_report_with_context(app):
    with app.app_context():
        generate_report()
