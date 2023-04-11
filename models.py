from flask_sqlalchemy import SQLAlchemy


#Here we have defined the models for the database

db = SQLAlchemy()


class StoreTimezone(db.Model):
    store_id = db.Column(db.Integer, primary_key=True)
    timezone_str = db.Column(db.String)


class StoreStatus(db.Model):
    store_id = db.Column(db.Integer)
    timestamp_utc = db.Column(db.DateTime)
    status = db.Column(db.String)
    __table_args__ = (db.PrimaryKeyConstraint('store_id', 'timestamp_utc'), )


class StoreHours(db.Model):
    store_id = db.Column(db.Integer)
    day = db.Column(db.Integer)
    start_time_local = db.Column(db.Time)
    end_time_local = db.Column(db.Time)
    __table_args__ = (db.PrimaryKeyConstraint(
        'store_id', 'day', 'start_time_local', 'end_time_local'),)
