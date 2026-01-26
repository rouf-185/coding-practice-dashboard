"""
Flask extensions initialization.

Extensions are initialized here without the app instance,
then bound to the app in the factory function.
"""
from flask_sqlalchemy import SQLAlchemy

# Database
db = SQLAlchemy()
