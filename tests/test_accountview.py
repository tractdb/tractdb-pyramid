import requests
import unittest

URL_BASE = 'http://localhost:8080'

TEST_ACCOUNT = 'testaccountview_account'
TEST_ACCOUNT_PASSWORD = 'testaccountview_password'
TEST_ROLE = 'testaccountview_role'


class TestAccountView(unittest.TestCase):
    def setUp(self):
        # Ensure the account does not already exist
        # (this could fail silently if the account doesn't exist)
        requests.delete(
            '{}/account/{}'.format(
                URL_BASE,
                TEST_ACCOUNT
            )
        )

    def test_create_and_delete_account(self):
        # Create the account
        r = requests.post(
            '{}/{}'.format(
                URL_BASE,
                'accounts'
            ),
            json={
                'account': TEST_ACCOUNT,
                'password': TEST_ACCOUNT_PASSWORD
            }
        )
        self.assertEqual(r.status_code, 201)

        # Test the creating it again fails
        r = requests.post(
            '{}/{}'.format(
                URL_BASE,
                'accounts'
            ),
            json={
                'account': TEST_ACCOUNT,
                'password': TEST_ACCOUNT_PASSWORD
            }
        )
        self.assertEqual(r.status_code, 409)

        # Test the account exists
        r = requests.get(
            '{}/{}'.format(
                URL_BASE,
                'accounts'
            )
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn(TEST_ACCOUNT, r.json()['accounts'])

        # Test reset password
        r = requests.post(
            '{}/{}'.format(
                URL_BASE,
                'reset_password'
            ),
            json={
                'account': TEST_ACCOUNT,
                'password': 'new_password'
            }
        )
        self.assertEqual(r.status_code, 201)

        # Delete the account
        r = requests.delete(
            '{}/{}/{}'.format(
                URL_BASE,
                'account',
                TEST_ACCOUNT
            )
        )
        self.assertEqual(r.status_code, 200)

        # Test that deleting the account again fails
        r = requests.delete(
            '{}/{}/{}'.format(
                URL_BASE,
                'account',
                TEST_ACCOUNT
            )
        )
        self.assertEqual(r.status_code, 404)

        # Test the account is gone
        r = requests.get(
            '{}/{}'.format(
                URL_BASE,
                'accounts'
            )
        )
        self.assertEqual(r.status_code, 200)
        self.assertNotIn(TEST_ACCOUNT, r.json()['accounts'])

    def test_create_and_delete_role(self):
        # Create the account
        r = requests.post(
            '{}/{}'.format(
                URL_BASE,
                'accounts'
            ),
            json={
                'account': TEST_ACCOUNT,
                'password': TEST_ACCOUNT_PASSWORD
            }
        )
        self.assertEqual(r.status_code, 201)

        # Ensure the role does not already exist
        r = requests.get(
            '{}/{}/{}/{}'.format(
                URL_BASE,
                'account',
                TEST_ACCOUNT,
                'roles'
            )
        )
        self.assertEqual(r.status_code, 200)
        self.assertNotIn(TEST_ROLE, r.json()['roles'])

        # Add role
        r = requests.post(
            '{}/{}/{}/{}'.format(
                URL_BASE,
                'account',
                TEST_ACCOUNT,
                'roles'
            ),
            json={
                'account': TEST_ACCOUNT,
                'role': TEST_ROLE
            }
        )
        self.assertEqual(r.status_code, 201)

        # Test that adding the role again fails
        r = requests.post(
            '{}/{}/{}/{}'.format(
                URL_BASE,
                'account',
                TEST_ACCOUNT,
                'roles'
            ),
            json={
                'account': TEST_ACCOUNT,
                'role': TEST_ROLE
            }
        )
        self.assertEqual(r.status_code, 409)

        # Test the role exists
        r = requests.get(
            '{}/{}/{}/{}'.format(
                URL_BASE,
                'account',
                TEST_ACCOUNT,
                'roles'
            )
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn(TEST_ROLE, r.json()['roles'])

        # Delete the role
        r = requests.delete(
            '{}/{}/{}/{}/{}'.format(
                URL_BASE,
                'account',
                TEST_ACCOUNT,
                'role',
                TEST_ROLE
            )
        )
        self.assertEqual(r.status_code, 200)

        # Test that deleting the role again fails
        r = requests.delete(
            '{}/{}/{}/{}/{}'.format(
                URL_BASE,
                'account',
                TEST_ACCOUNT,
                'role',
                TEST_ROLE
            )
        )
        self.assertEqual(r.status_code, 404)

        # Ensure the role does not exist
        r = requests.get(
            '{}/{}/{}/{}'.format(
                URL_BASE,
                'account',
                TEST_ACCOUNT,
                'roles'
            )
        )
        self.assertNotIn(TEST_ROLE, r.json()['roles'])

        # Delete the account
        r = requests.delete(
            '{}/{}/{}'.format(
                URL_BASE,
                'account',
                TEST_ACCOUNT
            )
        )
        self.assertEqual(r.status_code, 200)