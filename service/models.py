"""
Models for Account

All of the models are stored in this module.
"""
import logging
from datetime import date

from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger("flask.app")

# SQLAlchemy object to be initialized in init_db()
db = SQLAlchemy()


class DataValidationError(Exception):
    """Used for any data validation errors when deserializing."""


def init_db(app):
    """Initialize the SQLAlchemy app and create tables.

    This module-level function is provided because some tests import
    `init_db` directly from service.models.
    """
    db.init_app(app)
    # Attach the app to db so db.get_app() can find it without a context.
    db.app = app
    with app.app_context():
        db.create_all()


######################################################################
#  P E R S I S T E N T   B A S E   M O D E L
######################################################################
class PersistentBase:
    """Base class providing persistent methods."""

    def __init__(self):
        self.id = None  # pylint: disable=invalid-name

    def create(self):
        """Creates an Account in the database."""
        logger.info("Creating %s", getattr(self, "name", "<unknown>"))
        self.id = None  # ensure id is None to generate a new primary key
        db.session.add(self)
        db.session.commit()

    def update(self):
        """Updates an Account in the database."""
        logger.info("Updating %s", getattr(self, "name", "<unknown>"))
        db.session.commit()

    def delete(self):
        """Removes an Account from the data store."""
        logger.info("Deleting %s", getattr(self, "name", "<unknown>"))
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def all(cls):
        """Returns all of the records in the database."""
        logger.info("Processing all records")
        return cls.query.all()

    @classmethod
    def find(cls, by_id):
        """Finds a record by its ID."""
        logger.info("Processing lookup for id %s ...", by_id)
        return cls.query.get(by_id)


######################################################################
#  A C C O U N T   M O D E L
######################################################################
class Account(db.Model, PersistentBase):
    """Class that represents an Account."""

    # Table Schema
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    email = db.Column(db.String(64))
    address = db.Column(db.String(256))
    phone_number = db.Column(db.String(32), nullable=True)
    # Use callable default to avoid one-time evaluation at import time
    date_joined = db.Column(db.Date(), nullable=False, default=date.today)

    def __repr__(self):
        return f"<Account {self.name} id=[{self.id}]>"

    def serialize(self):
        """Serializes an Account into a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "address": self.address,
            "phone_number": self.phone_number,
            "date_joined": self.date_joined.isoformat(),
        }

    def deserialize(self, data):
        """Deserializes an Account from a dictionary."""
        try:
            self.name = data["name"]
            self.email = data["email"]
            self.address = data["address"]
            self.phone_number = data.get("phone_number")
            date_joined = data.get("date_joined")
            if date_joined:
                self.date_joined = date.fromisoformat(date_joined)
            else:
                self.date_joined = date.today()
        except KeyError as error:
            raise DataValidationError(
                "Invalid Account: missing " + error.args[0]
            ) from error
        except TypeError as error:
            raise DataValidationError(
                "Invalid Account: body of request contained bad or no "
                "data - " + str(error)
            ) from error
        return self

    @classmethod
    def find_by_name(cls, name):
        """Returns all Accounts with the given name."""
        logger.info("Processing name query for %s ...", name)
        return cls.query.filter(cls.name == name)

    @classmethod
    def init_db(cls, app):
        """Initialize DB for this model (keeps backwards compatibility).

        Some test files call Account.init_db(app). Provide this method
        so both module-level init_db and Account.init_db work.
        """
        db.init_app(app)
        # Attach the app so db.get_app() finds it without a context.
        db.app = app
        with app.app_context():
            db.create_all()
