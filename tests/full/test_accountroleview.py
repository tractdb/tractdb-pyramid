import nose.tools
import tests.utilities


class TestAccountRoleView:
    @classmethod
    def setup_class(cls):
        cls.utilities = tests.utilities.Utilities('TestAccountRoleView')

        # Ensure we have a test account
        cls.utilities.ensure_fresh_account(
            cls.utilities.test_account_name(),
            cls.utilities.test_account_password()
        )

        # Create a session for the account
        cls.session = cls.utilities.session_pyramid(
            cls.utilities.test_account_name(),
            cls.utilities.test_account_password()
        )

    @classmethod
    def teardown_class(cls):
        # Clean up our account
        cls.utilities.delete_account(
            cls.utilities.test_account_name()
        )

    def test_create_and_delete_role(self):
        cls = type(self)

        # Ensure the role does not already exist
        r = cls.session.get(
            '{}/{}/{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'account',
                cls.utilities.test_account_name(),
                'roles'
            )
        )
        nose.tools.assert_equal(r.status_code, 200)
        nose.tools.assert_not_in(cls.utilities.test_role(), r.json()['roles'])

        # Add role
        r = cls.session.post(
            '{}/{}/{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'account',
                cls.utilities.test_account_name(),
                'roles'
            ),
            json={
                'role': cls.utilities.test_role()
            }
        )
        nose.tools.assert_equal(r.status_code, 201)

        # Test that adding the role again fails
        r = cls.session.post(
            '{}/{}/{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'account',
                cls.utilities.test_account_name(),
                'roles'
            ),
            json={
                'role': cls.utilities.test_role()
            }
        )
        nose.tools.assert_equal(r.status_code, 409)

        # Test the role exists
        r = cls.session.get(
            '{}/{}/{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'account',
                cls.utilities.test_account_name(),
                'roles'
            )
        )
        nose.tools.assert_equal(r.status_code, 200)
        nose.tools.assert_in(cls.utilities.test_role(), r.json()['roles'])

        # Delete the role
        r = cls.session.delete(
            '{}/{}/{}/{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'account',
                cls.utilities.test_account_name(),
                'role',
                cls.utilities.test_role()
            )
        )
        nose.tools.assert_equal(r.status_code, 200)

        # Test that deleting the role again fails
        r = cls.session.delete(
            '{}/{}/{}/{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'account',
                cls.utilities.test_account_name(),
                'role',
                cls.utilities.test_role()
            )
        )
        nose.tools.assert_equal(r.status_code, 404)

        # Ensure the role does not exist
        r = cls.session.get(
            '{}/{}/{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'account',
                cls.utilities.test_account_name(),
                'roles'
            )
        )
        nose.tools.assert_not_in(cls.utilities.test_role(), r.json()['roles'])
