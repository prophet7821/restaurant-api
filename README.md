
# API Documentation


## Setup and Uage

To set up and use this system, follow these steps:

- Clone this repository and navigate to the project directory.

- Install the required dependencies using `pip install -r requirements.txt`.
- Set up the database with the provided CSV data.
- Start the server.
- Trigger the report generation using the /trigger_report endpoint.
- Poll for the report status using the /get_report endpoint with the report_id.
- Download the generated report as a CSV file when it is ready.


## Variables

To run this project, you will need to add the following environment variables to your `config.py` file

`YOUR_DATABASE_URI` - The URL for your database.


## API Reference

#### Get report id

```http
  GET /trigger_report
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| None | None | Starts report generation and returns a `report_id` |

#### Get item

```http
  GET /get_report/<report_id>
```

| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `report_id`      | `string` | **Required**. Id of item to fetch. |


## Code Walkthrough

First we need to ingest the data from the CSV to a database, so I have chosen PostgresSQL. I use SQLAlchemy to define a schema, and then use pandas to convert csv to DataFrames and insert it into database.

Then the API call hits the `/trigger_report` endpoint,in the `app.py` file  which creates a random string as report_id, and starts the report generation process in a separate thread.

The report generation process takes place in the `report-generator` file in the `generate_report()` function. Now initially we queried all data into the code and did our computation, but as an improvement we have used SQL aggregate and window functions to move most of the data, in the database, making it much more time optimized.

Then we use that data to map it into a csv file.

Since report generation is a time intensive operation, we have created a API endpoint `get_report/<report_id>` which acceptss the report id and returns "Running" if the report generation is in progress, or will return the CSV file when it's complete.

