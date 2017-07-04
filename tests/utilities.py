import base.docker
import io
import nose.tools
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
import requests
import tractdb.client
import tractdb.server.accounts
import yaml


class Utilities:
    def __init__(self, context):
        self._context = context

    def assert_docs_equal_ignoring_id_rev(self, doc1, doc2):
        # Make copies
        doc1copy = dict(doc1)
        doc2copy = dict(doc2)

        # Remove id and rev fields
        doc1copy.pop('_id', None)
        doc1copy.pop('_rev', None)
        doc2copy.pop('_id', None)
        doc2copy.pop('_rev', None)

        # Assert they are equal
        nose.tools.assert_equal(doc1copy, doc2copy)

    @classmethod
    def client(cls, *, account, password):
        # Create the client
        client = tractdb.client.TractDBClient(
            tractdb_url=cls.url_base_pyramid(),
            account=account,
            password=password
        )

        return client

    def create_admin(self):
        # Parse our couchdb secrets
        with open('tests/test-secrets/couchdb.yml') as f:
            couchdb_secrets = yaml.safe_load(f)

        # Create an admin object
        admin = tractdb.server.accounts.AccountsAdmin(
            couchdb_url='http://{}:{}'.format(
                base.docker.machine_ip(),
                5984
            ),
            couchdb_admin=couchdb_secrets['admin']['user'],
            couchdb_admin_password=couchdb_secrets['admin']['password']
        )

        return admin

    def delete_account(self, account_name, admin=None):
        admin = admin if admin is not None else self.create_admin()

        # Delete the account if it exists
        if account_name in admin.list_accounts():
            admin.delete_account(account_name)

    def delete_all_documents(self, session):
        # Get the documents
        response = session.get(
            '{}/{}'.format(
                self.url_base_pyramid(),
                'documents'
            )
        )
        nose.tools.assert_equal(response.status_code, 200)

        # Recover them from the response
        docs = response.json()['documents']

        # Delete each of them
        for doc in docs:
            # Delete the document
            response = session.delete(
                '{}/{}/{}'.format(
                    self.url_base_pyramid(),
                    'document',
                    doc['_id']
                )
            )
            nose.tools.assert_equal(response.status_code, 200)

    def ensure_fresh_account(self, account_name, account_password, admin=None):
        admin = admin if admin is not None else self.create_admin()

        # Ensure the account does not already exist
        if account_name in admin.list_accounts():
            admin.delete_account(account_name)

        # Create the account we expect
        admin.create_account(account_name, account_password)

    def session_pyramid(self, account_name, account_password):
        # Create a session that is authenticated as the desired account
        session = requests.Session()

        # Login with the session
        response = session.post(
            '{}/{}'.format(
                self.url_base_pyramid(),
                'login'
            ),
            json={
                'account': account_name,
                'password': account_password
            }
        )
        nose.tools.assert_equal(response.status_code, 200)

        return session

    def test_account_name(self, account_index=0):
        return 'account_{}_{}'.format(
            self._context,
            account_index
        ).lower()

    def test_account_password(self, account_index=0):
        return 'password_{}_{}'.format(
            self._context,
            account_index
        ).lower()

    def test_attachment_name(self, attachment_index=0):
        return 'attachment_{}_{}'.format(
            self._context,
            attachment_index
        ).lower()

    def test_document(self, document_index=0):
        return {
            'test_field':
                'content_{}_{}'.format(
                    self._context,
                    document_index
                ),
            'another_test_field':
                'content_{}_{}'.format(
                    self._context,
                    document_index
                )
        }

    def test_document_id(self, document_index=0):
        return 'document_id_{}_{}'.format(
            self._context,
            document_index
        ).lower()

    def test_image_bytes(self, image_index=0):
        test_image = PIL.Image.new('RGBA', (1024, 1024))
        drawing = PIL.ImageDraw.Draw(test_image)

        drawing.text(
            (512, 512),
            '{}'.format(image_index)
        )

        image_bytes = io.BytesIO()
        test_image.save(image_bytes, 'png')
        image_bytes.seek(0)

        return image_bytes.getvalue()

    def test_role(self, role_index=0):
        return 'role_{}_{}'.format(
            self._context,
            role_index
        ).lower()

    @staticmethod
    def url_base_pyramid():
        return 'http://localhost:8080'
