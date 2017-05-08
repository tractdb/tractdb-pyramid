import base.docker
import nose.tools
import requests
import tractdb.server.accounts
import yaml

LOGIN_URL = 'http://localhost:8080/login'
AUTHENTICATED_URL = 'http://localhost:8080/authenticated'
LOGOUT_URL = 'http://localhost:8080/logout'

TEST_ACCOUNT = 'testauthenticationviews_account'
TEST_ACCOUNT_PASSWORD = 'testauthenticationviews_password'


class TestAuthenticationViews:
    @classmethod
    def setup_class(cls):
        # Parse our couchdb secrets
        with open('tests/test-secrets/couchdb_secrets.yml') as f:
            couchdb_secrets = yaml.safe_load(f)

        # Create our admin object
        admin = tractdb.server.accounts.AccountsAdmin(
            couchdb_url='http://{}:{}'.format(
                base.docker.machine_ip(),
                5984
            ),
            couchdb_admin=couchdb_secrets['admin']['user'],
            couchdb_admin_password=couchdb_secrets['admin']['password']
        )

        # Create the account we expect
        if TEST_ACCOUNT not in admin.list_accounts():
            admin.create_account(TEST_ACCOUNT, TEST_ACCOUNT_PASSWORD)

    def test_authenticated(self):
        response = requests.get(
            AUTHENTICATED_URL
        )

        nose.tools.assert_equal(response.status_code, 403)

    def test_login(self):
        session = requests.Session()

        response = session.post(
            LOGIN_URL,
            json={
                'account': TEST_ACCOUNT,
                'password': TEST_ACCOUNT_PASSWORD
            }
        )
        nose.tools.assert_equal(response.status_code, 200)

        response = session.get(
            AUTHENTICATED_URL
        )
        nose.tools.assert_equal(response.status_code, 200)

        nose.tools.assert_equal(
            response.json()['account'],
            TEST_ACCOUNT
        )

    def test_login_fail(self):
        session = requests.Session()

        response = session.post(
            LOGIN_URL,
            json={
                'account': TEST_ACCOUNT,
                'password': 'invalid_password'
            }
        )
        nose.tools.assert_equal(response.status_code, 401)

    def test_logout(self):
        session = requests.Session()

        response = session.get(
            AUTHENTICATED_URL
        )
        nose.tools.assert_equal(response.status_code, 403)

        response = session.post(
            LOGIN_URL,
            json={
                'account': TEST_ACCOUNT,
                'password': TEST_ACCOUNT_PASSWORD
            }
        )
        nose.tools.assert_equal(response.status_code, 200)

        response = session.get(
            AUTHENTICATED_URL
        )
        nose.tools.assert_equal(response.status_code, 200)

        response = session.post(
            LOGOUT_URL
        )
        nose.tools.assert_equal(response.status_code, 200)

        response = session.get(
            AUTHENTICATED_URL
        )
        nose.tools.assert_equal(response.status_code, 403)
