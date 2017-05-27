import nose.tools
import requests
import tests.utilities


class TestAuthenticationView:
    @classmethod
    def setup_class(cls):
        cls.utilities = tests.utilities.Utilities('TestAuthenticationView')

        # Ensure we have a test account
        cls.utilities.ensure_fresh_account(
            cls.utilities.test_account_name(),
            cls.utilities.test_account_password()
        )

    @classmethod
    def teardown_class(cls):
        # Clean up our account
        cls.utilities.delete_account(
            cls.utilities.test_account_name()
        )

    def setup(self):
        cls = type(self)
        pass

    def teardown(self):
        cls = type(self)
        pass

    def test_authenticated_required(self):
        cls = type(self)

        # With a new session, this should fail because we're not authenticated
        session = requests.session()

        response = session.get(
            '{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'authenticated'
            )
        )

        nose.tools.assert_equal(response.status_code, 403)

    def test_login(self):
        cls = type(self)

        # Ensure we can login
        session = requests.Session()

        response = session.post(
            '{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'login'
            ),
            json={
                'account': cls.utilities.test_account_name(),
                'password': cls.utilities.test_account_password()
            }
        )
        nose.tools.assert_equal(response.status_code, 200)

        # Now we should be able to access
        response = session.get(
            '{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'authenticated'
            )
        )
        nose.tools.assert_equal(response.status_code, 200)

        # And it should confirm our login
        nose.tools.assert_equal(
            response.json()['account'],
            cls.utilities.test_account_name()
        )

    def test_login_fail(self):
        cls = type(self)

        # An invalid password should fail
        session = requests.Session()

        response = session.post(
            '{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'login'
            ),
            json={
                'account': cls.utilities.test_account_name(),
                'password': 'invalid_password'
            }
        )
        nose.tools.assert_equal(response.status_code, 401)

    def test_logout(self):
        cls = type(self)

        # Confirm that logging out means we lose access
        session = requests.Session()

        response = session.post(
            '{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'login'
            ),
            json={
                'account': cls.utilities.test_account_name(),
                'password': cls.utilities.test_account_password()
            }
        )
        nose.tools.assert_equal(response.status_code, 200)

        response = session.get(
            '{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'authenticated'
            )
        )
        nose.tools.assert_equal(response.status_code, 200)

        response = session.post(
            '{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'logout'
            )
        )
        nose.tools.assert_equal(response.status_code, 200)

        response = session.get(
            '{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'authenticated'
            )
        )
        nose.tools.assert_equal(response.status_code, 403)
