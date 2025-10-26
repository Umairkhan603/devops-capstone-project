"""
Models for Account

All of the models are stored in this module
"""
import logging
from datetime import date
from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger("flask.app")

# Create the SQLAlchemy object to be initialized later
db = SQLAlchemy()


class DataValidationError(Exception):
    """Used for any data validation errors when deserializing."""


def init_db(app):
    """Initialize the SQLAlchemy app and create tables."""
    db.init_app(app)
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
        """Creates a record in the database."""
        logger.info("Creating record: %s", getattr(self, "name", "unknown"))
        self.id = None  # id must be None to generate a new primary key
        db.session.add(self)
        db.session.commit()

    def update(self):
        """Updates a record in the database."""
        logger.info("Updating record: %s", getattr(self, "name", "unknown"))
        db.session.commit()

    def delete(self):
        """Removes a record from the data store."""
        logger.info("Deleting record: %s", getattr(self, "name", "unknown"))
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def all(cls):
        """Returns all of the records in the database."""
        logger.info("Fetching all records for %s", cls.__name__)
        return cls.query.all()

    @classmethod
    def find(cls, by_id):
        """Finds a record by its ID."""
        logger.info("Looking up %s by id=%s", cls.__name__, by_id)
        return cls.query.get(by_id)


######################################################################
#  A C C O U N T   M O D E L
######################################################################
class Account(db.Model, PersistentBase):
    """Class that represents an Account."""

    __tablename__ = "account"

    # Table Schema
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), nullable=False)
    address = db.Column(db.String(256), nullable=False)
    phone_number = db.Column(db.String(32), nullable=True)  # optional
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
                f"Invalid Account: missing {error.args[0]}"
            ) from error
        except TypeError as error:
            raise DataValidationError(
                f"Invalid Account: bad or no data - {error.args[0]}"
            ) from error

        return self

    @classmethod
    def find_by_name(cls, name):
        """Returns all Accounts with the given name."""
        logger.info("Querying for accounts with name=%s", name)
        return cls.query.filter(cls.name == name)

    @staticmethod
    def init_db(app):
        """Initializes the database with the given Flask app."""
        db.init_app(app)
        with app.app_context():
            db.create_all()
