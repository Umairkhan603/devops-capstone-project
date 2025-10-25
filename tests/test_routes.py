"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"


######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ADD YOUR TEST CASES HERE ...
    def test_read_an_account(self):
        """It should Read a single Account"""
        # Create one account
        account = self._create_accounts(1)[0]

        # Send GET request to retrieve it
        resp = self.client.get(f"{BASE_URL}/{account.id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.get_json()
        self.assertEqual(data["name"], account.name)
        self.assertEqual(data["email"], account.email)
        self.assertEqual(data["address"], account.address)
        self.assertIn("id", data)


    def test_read_account_not_found(self):
        """It should return 404 if the account does not exist"""
        resp = self.client.get(f"{BASE_URL}/9999")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        data = resp.get_json()
        self.assertIn("not found", data["message"].lower())
    
    def test_read_account_logs_and_response_fields(self):
        """It should log and return all expected fields for a valid account"""
        account = self._create_accounts(1)[0]
        resp = self.client.get(f"{BASE_URL}/{account.id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        # Check all fields exist and are correct
        self.assertIn("id", data)
        self.assertIn("name", data)
        self.assertIn("email", data)
        self.assertIn("address", data)
        self.assertEqual(data["id"], account.id)
        self.assertEqual(data["name"], account.name)

    def test_create_account_with_invalid_content_type(self):
        """It should return 415 when Content-Type is not application/json"""
        resp = self.client.post(
            BASE_URL,
            json={"name": "Invalid User", "email": "invalid@example.com"},
            headers={"Content-Type": "text/plain"}
        )
        self.assertEqual(resp.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_list_accounts_returns_empty_list(self):
        """It should return an empty list when no accounts exist"""
        resp = self.client.get(BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data, [])

    def test_list_multiple_accounts(self):
        """It should List multiple accounts"""
        # Create multiple accounts
        self._create_accounts(3)

        # Send GET request to list all
        resp = self.client.get(BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 3)
        self.assertIn("name", data[0])
        self.assertIn("email", data[0])
        self.assertIn("address", data[0])
        self.assertIn("id", data[0])

    def test_update_account(self):
        """It should Update an existing Account"""
        account = self._create_accounts(1)[0]

        updated_data = {
            "name": "Updated Name",
            "email": "updated@example.com",
            "address": "New Address 123",
            "phone_number": "9876543210",
            "date_joined": str(account.date_joined),
        }

        resp = self.client.put(
            f"{BASE_URL}/{account.id}",
            json=updated_data,
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["name"], updated_data["name"])
        self.assertEqual(data["email"], updated_data["email"])

    def test_update_nonexistent_account(self):
        """It should return 404 when trying to update a non-existing Account"""
        updated_data = {"name": "Ghost"}
        resp = self.client.put(f"{BASE_URL}/9999", json=updated_data)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
