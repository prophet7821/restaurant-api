import pandas as pd
from models import db


def read_and_store_csv_with_context(app):
    with app.app_context():
        read_and_store_csv()


# This function is called from the ingest_data() function
# It reads the csv files and stores them in the database
def read_and_store_csv():
    store_status_df = pd.read_csv('store_status.csv', parse_dates=['timestamp_utc'])
    store_hours_df = pd.read_csv('store_hours.csv')
    store_timezone_df = pd.read_csv('store_timezone.csv')

    store_status_df.to_sql('store_status', db.engine,
                           if_exists='append', index=False)
    store_hours_df.to_sql('store_hours', db.engine,
                          if_exists='append', index=False)
    store_timezone_df.to_sql('store_timezone', db.engine,
                             if_exists='append', index=False)
