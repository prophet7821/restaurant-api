# Description: Generates a report of uptime and downtime for each store
# This generate report function is used to generate a report of uptime and downtime for each store. 
# The report is generated by querying the database for the store status, store hours, and store timezone. 
# The report is then generated by iterating through each store and calculating the uptime and downtime for each store. 
# The report is then returned as a dictionary.

from typing import Dict
from models import StoreStatus, StoreHours, StoreTimezone, db
from sqlalchemy import text


def generate_report() -> Dict[int, Dict[str, float]]:
    report = {}


#The SQL query uses aggregate functions to calculate the uptime and downtime for each store.
#We are using this approach to reduce data transfer between the database and the application,
#thus handliing most of the computation in the database.

    sql_query = text("""
  WITH
    store_timezones_filled AS (
    SELECT
        store_id,
        COALESCE(timezone_str, 'America/Chicago') AS timezone_str
    FROM store_timezone
),
     store_hours_filled AS (
         SELECT
             store_id,
             day,
             COALESCE(start_time_local, '00:00:00') AS start_time_local,
             COALESCE(end_time_local, '23:59:59') AS end_time_local
         FROM store_hours
         UNION ALL
         SELECT
             store_timezones_filled.store_id,
             s.day,
             '00:00:00' AS start_time_local,
             '23:59:59' AS end_time_local
         FROM store_timezones_filled
                  CROSS JOIN (SELECT generate_series(0, 6) AS day) AS s
         WHERE NOT EXISTS (SELECT 1 FROM store_hours WHERE store_hours.store_id = store_timezones_filled.store_id)
     ),
     store_hours_utc AS (SELECT store_hours_filled.store_id,
                                start_time_local::time AT TIME ZONE store_timezones_filled.timezone_str AT TIME ZONE
                                'UTC' AS start_time_utc,
                                end_time_local::time AT TIME ZONE store_timezones_filled.timezone_str AT TIME ZONE
                                'UTC' AS end_time_utc,
                                store_hours_filled.day
                         FROM store_hours_filled
                                  JOIN store_timezones_filled
                                       ON store_timezones_filled.store_id = store_hours_filled.store_id),
     store_status_lag AS (

     SELECT
         store_status.store_id,
        store_status.status,
        store_status.timestamp_utc,
        LAG(store_status.timestamp_utc::timestamp) OVER (PARTITION BY store_status.store_id ORDER BY store_status.timestamp_utc::timestamp) AS prev_timestamp_utc
    FROM store_status
    JOIN store_hours_utc ON store_hours_utc.store_id = store_status.store_id
    WHERE EXTRACT(DOW FROM store_status.timestamp_utc::timestamp) = store_hours_utc.day
    AND store_status.timestamp_utc::time BETWEEN store_hours_utc.start_time_utc AND store_hours_utc.end_time_utc
    --AND store_status.timestamp_utc::timestamp >= NOW() - INTERVAL '1 week'
    )


SELECT
    store_id,
    status,
    SUM(EXTRACT(EPOCH FROM (COALESCE(timestamp_utc::timestamp, NOW()) - COALESCE(prev_timestamp_utc, timestamp_utc::timestamp))) / 60) FILTER (WHERE now() - timestamp_utc::timestamp < INTERVAL '1 hour') AS duration_last_hour_minutes,
    SUM(EXTRACT(EPOCH FROM (COALESCE(timestamp_utc::timestamp, NOW()) - COALESCE(prev_timestamp_utc, timestamp_utc::timestamp))) / 60) FILTER (WHERE now() - timestamp_utc::timestamp < INTERVAL '1 day') AS duration_last_day_minutes,
    SUM(EXTRACT(EPOCH FROM (COALESCE(timestamp_utc::timestamp, NOW()) - COALESCE(prev_timestamp_utc, timestamp_utc::timestamp))) / 60) FILTER (WHERE now() - timestamp_utc::timestamp < INTERVAL '1 week') AS duration_last_week_minutes
FROM store_status_lag
WHERE prev_timestamp_utc IS NOT NULL
GROUP BY store_id, status
ORDER BY store_id;
""")

    connection = db.engine.connect()
    store_data_query = connection.execute(sql_query)
    data_dict = store_data_query.mappings().all()
    connection.close()
    
    
    #We read the data that was returned from the database and store it in a dictionary.

    for row in data_dict:
        if row.store_id not in report:
            report[row.store_id] = {'uptime_last_hour': 0, 'uptime_last_day': 0, 'uptime_last_week': 0,
                                    'downtime_last_hour': 0, 'downtime_last_day': 0, 'downtime_last_week': 0}

        if row.status == 'active':
            report[row.store_id]['uptime_last_hour'] = row.duration_last_hour_minutes if row.duration_last_hour_minutes else 0
            report[row.store_id]['uptime_last_day'] = (
                row.duration_last_day_minutes if row.duration_last_day_minutes else 0) * 60
            report[row.store_id]['uptime_last_week'] = (
                row.duration_last_week_minutes if row.duration_last_week_minutes else 0) * 60
        else:
            report[row.store_id]['downtime_last_hour'] = row.duration_last_hour_minutes if row.duration_last_hour_minutes else 0
            report[row.store_id]['downtime_last_day'] = (
                row.duration_last_day_minutes if row.duration_last_day_minutes else 0) * 60

            report[row.store_id]['downtime_last_week'] = (
                row.duration_last_week_minutes if row.duration_last_week_minutes else 0) * 60

    return report


def generate_report_with_context(app):
    with app.app_context():
        return generate_report()