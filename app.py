from flask import Flask, jsonify, send_file
from threading import Thread
import uuid
import csv

from models import db, StoreStatus, StoreHours, StoreTimezone
from config import Config
from report_generator import generate_report_with_context
from data_ingestion import read_and_store_csv_with_context

#This is the main flask app that will be responsible for handling the requests and returning the responses.
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
report_status = {}
report_data = {}
reports = {}




# This function will be resonsible for reading the csv file and storing the data in the database
@app.route('/ingest_data', methods=['GET'])
def ingest_data():
    read_and_store_csv_with_context(app)
    return jsonify(message="Data Ingestion Complete")


#This function will be responsible for generationg the report and returning a report id.
@app.route('/trigger_report', methods=['GET'])
def trigger_report():
    report_id = str(uuid.uuid4())
    report_status[report_id] = 'Running'

    #Starting the report generation in a separate thread so that the normal flow of the code is not blocked.
    def async_generate_report(report_id):
        report = generate_report_with_context(app)
        report_status[report_id] = 'Complete'
        report_data[report_id] = report
        print("Done")

    Thread(target=async_generate_report, args=(report_id,)).start()
    return jsonify(report_id=report_id)


@app.route('/get_report/<report_id>', methods=['GET'])
def get_report(report_id):
    status = report_status.get(report_id, 'Not Found')
    if status == 'Complete':
        #We create a csv file and read the dictionary sent to us by the report generator and write it to the csv file.
        output_file = f'report_{report_id}.csv'
        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['store_id', 'uptime_last_hour', 'uptime_last_day', 'uptime_last_week',
                             'downtime_last_hour', 'downtime_last_day', 'downtime_last_week'])
            for store_id, data in report_data[report_id].items():
                writer.writerow([store_id] + list(data.values()))
        print("Now sending file")
        return send_file(output_file, mimetype='text/csv', download_name="report.csv", as_attachment=True)

    else:
        return jsonify(status=status)


if __name__ == '__main__':
    app.run()
