import base.docker
import nose.tools
import requests
import tractdb.server.accounts
import yaml

URL_BASE = 'http://localhost:8080'

TEST_ACCOUNT = 'testdocumentviews_account'
TEST_ACCOUNT_PASSWORD = 'testdocumentviews_password'

TEST_DOCUMENT = {
    'text': 'some content',
    'date': '03/20/2017'
}

TEST_DOCUMENT_DIFFERENT = {
    'text': 'some different content',
    'date': '03/20/2017'
}


class TestDocumentViews:
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
        if TEST_ACCOUNT in admin.list_accounts():
            admin.delete_account(TEST_ACCOUNT)
        admin.create_account(TEST_ACCOUNT, TEST_ACCOUNT_PASSWORD)

    def test_create_get_delete_document(self):
        session = requests.Session()

        # Login with the session
        response = session.post(
            '{}/{}'.format(
                URL_BASE,
                'login'
            ),
            json={
                'account': TEST_ACCOUNT,
                'password': TEST_ACCOUNT_PASSWORD
            }
        )
        nose.tools.assert_equal(response.status_code, 200)

        # Create a document
        response_post = session.post(
            '{}/{}'.format(
                URL_BASE,
                'documents'
            ),
            json={
                'document': TEST_DOCUMENT
            }
        )
        nose.tools.assert_equal(response_post.status_code, 201)

        # The location header should contain a URL to the created document
        nose.tools.assert_in('Location', response_post.headers)
        response = session.get(
            response_post.headers['Location']
        )
        nose.tools.assert_equal(response.status_code, 200)
        doc = response.json()

        # Remove the internal fields for comparison
        doc = dict(doc)
        del doc['_id']
        del doc['_rev']
        nose.tools.assert_equal(doc, TEST_DOCUMENT)

        # The body should include an ID too
        body = response_post.json()
        nose.tools.assert_in('id', body)
        doc_id = body['id']

        # Also get the document via that
        response = session.get(
            '{}/{}/{}'.format(
                URL_BASE,
                'document',
                doc_id
            )
        )
        nose.tools.assert_equal(response.status_code, 200)
        doc = response.json()

        # Remove the internal fields for comparison
        doc = dict(doc)
        del doc['_id']
        del doc['_rev']
        nose.tools.assert_equal(doc, TEST_DOCUMENT)

        # Delete the document
        response = session.delete(
            '{}/{}/{}'.format(
                URL_BASE,
                'document',
                doc_id
            )
        )
        nose.tools.assert_equal(response.status_code, 200)

        # Confirm it's not there anymore
        response = session.get(
            '{}/{}/{}'.format(
                URL_BASE,
                'document',
                doc_id
            )
        )
        nose.tools.assert_equal(response.status_code, 404)

    def test_get_documents(self):
        session = requests.Session()

        # Login with the session
        response = session.post(
            '{}/{}'.format(
                URL_BASE,
                'login'
            ),
            json={
                'account': TEST_ACCOUNT,
                'password': TEST_ACCOUNT_PASSWORD
            }
        )
        nose.tools.assert_equal(response.status_code, 200)

        # Create a document
        response = session.post(
            '{}/{}'.format(
                URL_BASE,
                'documents'
            ),
            json={
                'document': TEST_DOCUMENT
            }
        )
        nose.tools.assert_equal(response.status_code, 201)

        # Create another document
        response = session.post(
            '{}/{}'.format(
                URL_BASE,
                'documents'
            ),
            json={
                'document': TEST_DOCUMENT_DIFFERENT
            }
        )
        nose.tools.assert_equal(response.status_code, 201)

        # Ensure we get just these two documents
        response = session.get(
            '{}/{}'.format(
                URL_BASE,
                'documents'
            )
        )
        nose.tools.assert_equal(response.status_code, 200)

        # The right number of documents
        docs = response.json()['documents']

        print(docs, flush=True)

        nose.tools.assert_equal(len(docs), 2)

        # The right documents
        docs = [dict(doc) for doc in docs]
        for doc in docs:
            del doc['_id']
            del doc['_rev']
        docs.remove(TEST_DOCUMENT)
        docs.remove(TEST_DOCUMENT_DIFFERENT)
        nose.tools.assert_equal(len(docs), 0)
