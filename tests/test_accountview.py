import requests
import unittest

TEST_ACCOUNT = 'testaccountview_account'
TEST_ACCOUNT_PASSWORD = 'testaccountview_password'
TEST_ROLE = 'testaccountview-role'

ACCOUNT_URL = 'http://localhost:8080/account'
ACCOUNT_COLLECTION_URL = 'http://localhost:8080/accounts'
ROLE_COLLECTION_URL = 'http://localhost:8080/account/'+TEST_ACCOUNT+'/roles'
ROLE_URL = 'http://localhost:8080/account/'+TEST_ACCOUNT+'/roles/'+TEST_ROLE


class TestAccountView(unittest.TestCase):
    def test_create_and_delete_account(self):
        # Get the current accounts
        r = requests.get(
            ACCOUNT_COLLECTION_URL,
        )
        self.assertEqual(r.status_code, 200)

        # Ensure it does not already exist (this could fail silently if the account doesn't exist)
        r = requests.delete(
            '{}/{}'.format(
                ACCOUNT_URL,
                TEST_ACCOUNT
            )
        )

        # Create the account
        r = requests.post(
            ACCOUNT_COLLECTION_URL,
            json={
                'account': TEST_ACCOUNT,
                'password': TEST_ACCOUNT_PASSWORD
            }
        )
        self.assertEqual(r.status_code, 201)

        # Test the creating it again fails
        r = requests.post(
            ACCOUNT_COLLECTION_URL,
            json={
                'account': TEST_ACCOUNT,
                'password': TEST_ACCOUNT_PASSWORD
            }
        )
        self.assertEqual(r.status_code, 409)

        # Test the account exists
        r = requests.get(
            ACCOUNT_COLLECTION_URL,
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn(TEST_ACCOUNT, r.json()['accounts'])

        # Delete the account
        r = requests.delete(
            '{}/{}'.format(
                ACCOUNT_URL,
                TEST_ACCOUNT
            )
        )
        self.assertEqual(r.status_code, 200)

        # Test that deleting the account again fails
        r = requests.delete(
            '{}/{}'.format(
                ACCOUNT_URL,
                TEST_ACCOUNT
            )
        )
        self.assertEqual(r.status_code, 404)

        # Test the account is gone
        r = requests.get(
            ACCOUNT_COLLECTION_URL,
        )
        self.assertEqual(r.status_code, 200)
        self.assertNotIn(TEST_ACCOUNT, r.json()['accounts'])

    def test_create_and_delete_role(self):
        # Get the current accounts
        r = requests.get(
            ACCOUNT_COLLECTION_URL,
        )
        self.assertEqual(r.status_code, 200)

        # Ensure it does not already exist (this could fail silently if the account doesn't exist)
        r = requests.delete(
            '{}/{}'.format(
                ACCOUNT_URL,
                TEST_ACCOUNT
            )
        )

        # Create the account
        r = requests.post(
            ACCOUNT_COLLECTION_URL,
            json={
                'account': TEST_ACCOUNT,
                'password': TEST_ACCOUNT_PASSWORD
            }
        )
        self.assertEqual(r.status_code, 201)

        # Ensure the role does not exist
        r = requests.get(
            ROLE_COLLECTION_URL,
        )
        self.assertEqual(r.status_code, 200)

        # Add role
        r = requests.post(
            ROLE_COLLECTION_URL,
            json={
                'account': TEST_ACCOUNT,
                'role': TEST_ROLE
            }
        )
        self.assertEqual(r.status_code, 201)

        # Test the role exists
        r = requests.get(
            ROLE_COLLECTION_URL,
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn(TEST_ROLE, r.json()['roles'])

        # Delete the role
        r = requests.delete(
            '{}/{}'.format(
                ROLE_COLLECTION_URL,
                TEST_ROLE
            )
        )
        self.assertEqual(r.status_code, 200)

        # Ensure the role does not exist
        r = requests.get(
            ROLE_COLLECTION_URL,
        )
        self.assertNotIn(TEST_ROLE, r.json()['roles'])

        # Delete the account
        r = requests.delete(
            '{}/{}'.format(
                ACCOUNT_URL,
                TEST_ACCOUNT
            )
        )
        self.assertEqual(r.status_code, 200)

        # Test that deleting the account again fails
        r = requests.delete(
            '{}/{}'.format(
                ACCOUNT_URL,
                TEST_ACCOUNT
            )
        )
        self.assertEqual(r.status_code, 404)

        # Test the account is gone
        r = requests.get(
            ACCOUNT_COLLECTION_URL,
        )
        self.assertEqual(r.status_code, 200)
        self.assertNotIn(TEST_ACCOUNT, r.json()['accounts'])

