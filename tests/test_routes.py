"""
Account API Service Test Suite

Test cases can be run with:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status
from service.models import db, Account, init_db
from service.routes import app
from service import talisman

DATABASE_URI = os.getenv(
    "DATABASE_URI",
    "postgresql://postgres:postgres@localhost:5432/postgres",
)

BASE_URL = "/accounts"
HTTPS_ENVIRON = {"wsgi.url_scheme": "https"}


class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        talisman.force_https = False
        app.logger.setLevel(logging.CRITICAL)
        with app.app_context():
            init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def setUp(self):
        """Runs before each test"""
        with app.app_context():
            db.session.query(Account).delete()
            db.session.commit()
        self.client = app.test_client()

    def tearDown(self):
        """Runs after each test"""
        with app.app_context():
            db.session.remove()

    ######################################################################
    #  HELPER METHOD
    ######################################################################
    def _create_accounts(self, count):
        """Helper to bulk create accounts"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    # TEST CASES
    ######################################################################
    def test_index(self):
        """It should return 200_OK on home page"""
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
        resp = self.client.post(BASE_URL, json=account.serialize())
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        location = resp.headers.get("Location", None)
        self.assertIsNotNone(location)
        data = resp.get_json()
        self.assertEqual(data["name"], account.name)
        self.assertEqual(data["email"], account.email)
        self.assertEqual(data["address"], account.address)
        self.assertEqual(data["phone_number"], account.phone_number)
        self.assertEqual(data["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create Account with invalid data"""
        resp = self.client.post(BASE_URL, json={"name": "invalid"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should reject wrong content type"""
        account = AccountFactory()
        resp = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="text/html",
        )
        self.assertEqual(
            resp.status_code,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )

    def test_read_an_account(self):
        """It should Read a single Account"""
        account = self._create_accounts(1)[0]
        resp = self.client.get(f"{BASE_URL}/{account.id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["name"], account.name)
        self.assertEqual(data["email"], account.email)
        self.assertEqual(data["address"], account.address)
        self.assertIn("id", data)

    def test_read_account_not_found(self):
        """It should return 404 for missing Account"""
        resp = self.client.get(f"{BASE_URL}/9999")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        data = resp.get_json()
        self.assertIn("not found", data["message"].lower())

    def test_list_accounts_returns_empty_list(self):
        """It should return empty list if no accounts"""
        resp = self.client.get(BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.get_json(), [])

    def test_list_multiple_accounts(self):
        """It should List multiple Accounts"""
        self._create_accounts(3)
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
        """It should Update an Account"""
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
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["name"], updated_data["name"])
        self.assertEqual(data["email"], updated_data["email"])

    def test_update_nonexistent_account(self):
        """It should return 404 for non-existent update"""
        resp = self.client.put(f"{BASE_URL}/9999", json={"name": "Ghost"})
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_account(self):
        """It should Delete an Account"""
        account = self._create_accounts(1)[0]
        resp = self.client.delete(f"{BASE_URL}/{account.id}")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        get_resp = self.client.get(f"{BASE_URL}/{account.id}")
        self.assertEqual(get_resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_nonexistent_account(self):
        """It should return 204 for non-existent delete"""
        resp = self.client.delete(f"{BASE_URL}/9999")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_security_headers(self):
        """It should return security headers"""
        resp = self.client.get("/", environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        headers = {
            "X-Frame-Options": "SAMEORIGIN",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy":
                "default-src 'self'; object-src 'none'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }
        for key, value in headers.items():
            self.assertEqual(resp.headers.get(key), value)

    def test_cors_security(self):
        """It should return CORS header"""
        resp = self.client.get("/", environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.headers.get("Access-Control-Allow-Origin"), "*")
