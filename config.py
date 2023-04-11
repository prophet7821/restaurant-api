# Description: Configuration file for the Flask app

class Config:
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgrespw@localhost:49153'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
