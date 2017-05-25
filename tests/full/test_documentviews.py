import base.docker
import nose.tools
import requests
import tractdb.server.accounts
import yaml

URL_BASE = 'http://localhost:8080'

TEST_ACCOUNT = 'testdocumentviews_account'
TEST_ACCOUNT_PASSWORD = 'testdocumentviews_password'

TEST_DOCUMENT_ID = 'test_document_id'

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
        with open('tests/test-secrets/couchdb.yml') as f:
            couchdb_secrets = yaml.safe_load(f)

        # Create an admin object that can manage accounts
        admin = tractdb.server.accounts.AccountsAdmin(
            couchdb_url='http://{}:{}'.format(
                base.docker.machine_ip(),
                5984
            ),
            couchdb_admin=couchdb_secrets['admin']['user'],
            couchdb_admin_password=couchdb_secrets['admin']['password']
        )

        # Ensure the account does not already exist
        if TEST_ACCOUNT in admin.list_accounts():
            admin.delete_account(TEST_ACCOUNT)

        # Create the account we expect
        admin.create_account(TEST_ACCOUNT, TEST_ACCOUNT_PASSWORD)

        # Create a session that is authenticated as this account

    def test_create_document_with_id_via_path(self):
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

        # Our test id
        doc_id = TEST_DOCUMENT_ID

        # Create a document with a particular ID
        response_post = session.post(
            '{}/{}/{}'.format(
                URL_BASE,
                'document',
                doc_id
            ),
            json=TEST_DOCUMENT
        )
        nose.tools.assert_equal(response_post.status_code, 201)

        # Get the document via that ID
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

        # Try creating it again
        response_post = session.post(
            '{}/{}'.format(
                URL_BASE,
                'documents'
            ),
            json={
                'id': doc_id,
                'document': TEST_DOCUMENT
            }
        )
        nose.tools.assert_equal(response_post.status_code, 409)

        # Delete the document
        response = session.delete(
            '{}/{}/{}'.format(
                URL_BASE,
                'document',
                doc_id
            )
        )
        nose.tools.assert_equal(response.status_code, 200)

    def test_create_document_with_id_via_collection(self):
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

        # Our test id
        doc_id = TEST_DOCUMENT_ID

        # Create a document with a particular ID
        response_post = session.post(
            '{}/{}'.format(
                URL_BASE,
                'documents'
            ),
            json={
                'id': doc_id,
                'document': TEST_DOCUMENT
            }
        )
        nose.tools.assert_equal(response_post.status_code, 201)

        # Get the document via that ID
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

        # Try creating it again
        response_post = session.post(
            '{}/{}'.format(
                URL_BASE,
                'documents'
            ),
            json={
                'id': doc_id,
                'document': TEST_DOCUMENT
            }
        )
        nose.tools.assert_equal(response_post.status_code, 409)

        # Delete the document
        response = session.delete(
            '{}/{}/{}'.format(
                URL_BASE,
                'document',
                doc_id
            )
        )
        nose.tools.assert_equal(response.status_code, 200)

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

    def test_create_modify_document(self):
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

        # The body should include an ID too
        body = response_post.json()
        nose.tools.assert_in('id', body)
        doc_id = body['id']

        # Get the document
        response = session.get(
            '{}/{}/{}'.format(
                URL_BASE,
                'document',
                doc_id
            )
        )
        nose.tools.assert_equal(response.status_code, 200)
        doc = response.json()

        # Modify the document
        doc.update(TEST_DOCUMENT_DIFFERENT)

        # Put the modified version
        put_response = session.put(
            '{}/{}/{}'.format(
                URL_BASE,
                'document',
                doc_id
            ),
            json=doc
        )
        nose.tools.assert_equal(put_response.status_code, 200)

        # Update the rev with what we got back from the server
        doc['_rev'] = put_response.json()['rev']

        # Get the document again
        response = session.get(
            '{}/{}/{}'.format(
                URL_BASE,
                'document',
                doc_id
            )
        )
        nose.tools.assert_equal(response.status_code, 200)

        # Confirm they are the same
        nose.tools.assert_equal(doc, response.json())

        # Delete the document
        response = session.delete(
            '{}/{}/{}'.format(
                URL_BASE,
                'document',
                doc_id
            )
        )
        nose.tools.assert_equal(response.status_code, 200)

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
