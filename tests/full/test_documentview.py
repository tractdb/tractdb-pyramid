import nose.tools
import tests.utilities


class TestDocumentView:
    @classmethod
    def setup_class(cls):
        cls.utilities = tests.utilities.Utilities('TestDocumentView')

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

    def setup(self):
        cls = type(self)

        # Ensure no documents remain from prior tests
        cls.utilities.delete_all_documents(cls.session)

    def teardown(self):
        cls = type(self)

        # Clean up our documents
        cls.utilities.delete_all_documents(cls.session)

    def test_create_document_with_id_via_path(self):
        cls = type(self)
        session = cls.session

        # Create a document with a particular ID
        response_post = session.post(
            '{}/{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'document',
                cls.utilities.test_document_id()
            ),
            json=cls.utilities.test_document()
        )
        nose.tools.assert_equal(response_post.status_code, 201)

        # Get the document via that ID
        response = session.get(
            '{}/{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'document',
                cls.utilities.test_document_id()
            )
        )
        nose.tools.assert_equal(response.status_code, 200)
        doc = response.json()

        # Confirm it's our document
        cls.utilities.assert_docs_equal_ignoring_id_rev(
            doc,
            cls.utilities.test_document()
        )

        # Try creating it again, should fail because it already exists
        response_post = session.post(
            '{}/{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'document',
                cls.utilities.test_document_id()
            ),
            json=cls.utilities.test_document()
        )
        nose.tools.assert_equal(response_post.status_code, 409)

    def test_create_document_with_id_via_collection(self):
        cls = type(self)
        session = cls.session

        # Create a document with a particular ID
        response_post = session.post(
            '{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'documents'
            ),
            json={
                'id': cls.utilities.test_document_id(),
                'document': cls.utilities.test_document()
            }
        )
        nose.tools.assert_equal(response_post.status_code, 201)

        # Get the document via that ID
        response = session.get(
            '{}/{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'document',
                cls.utilities.test_document_id()
            )
        )
        nose.tools.assert_equal(response.status_code, 200)
        doc = response.json()

        # Confirm it's our document
        cls.utilities.assert_docs_equal_ignoring_id_rev(
            doc,
            cls.utilities.test_document()
        )

        # Try creating it again, should fail because it already exists
        response_post = session.post(
            '{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'documents'
            ),
            json={
                'id': cls.utilities.test_document_id(),
                'document': cls.utilities.test_document()
            }
        )
        nose.tools.assert_equal(response_post.status_code, 409)

    def test_create_get_delete_document(self):
        cls = type(self)
        session = cls.session

        # Create a document
        response_post = session.post(
            '{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'documents'
            ),
            json={
                'document': cls.utilities.test_document()
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

        # Confirm it's our document
        cls.utilities.assert_docs_equal_ignoring_id_rev(
            doc,
            cls.utilities.test_document()
        )

        # The body should include an ID too
        body = response_post.json()
        nose.tools.assert_in('_id', body)
        doc_id = body['_id']

        # Also get the document via that
        response = session.get(
            '{}/{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'document',
                doc_id
            )
        )
        nose.tools.assert_equal(response.status_code, 200)
        doc = response.json()

        # Confirm it's our document
        cls.utilities.assert_docs_equal_ignoring_id_rev(
            doc,
            cls.utilities.test_document()
        )

        # Delete the document
        response = session.delete(
            '{}/{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'document',
                doc_id
            )
        )
        nose.tools.assert_equal(response.status_code, 200)

        # Confirm it's not there anymore
        response = session.get(
            '{}/{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'document',
                doc_id
            )
        )
        nose.tools.assert_equal(response.status_code, 404)

    def test_create_modify_document(self):
        cls = type(self)
        session = cls.session

        # Create a document
        response_post = session.post(
            '{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'documents'
            ),
            json={
                'document': cls.utilities.test_document()
            }
        )
        nose.tools.assert_equal(response_post.status_code, 201)

        # Recover the ID of the created document
        body = response_post.json()
        nose.tools.assert_in('_id', body)
        doc_id = body['_id']

        # Get the document
        response = session.get(
            '{}/{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'document',
                doc_id
            )
        )
        nose.tools.assert_equal(response.status_code, 200)
        doc = response.json()

        # Modify the document
        doc.update(cls.utilities.test_document(1))

        # Put the modified version
        put_response = session.put(
            '{}/{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'document',
                doc_id
            ),
            json=doc
        )
        nose.tools.assert_equal(put_response.status_code, 200)

        # Update the rev with what we got back from the server
        doc['_rev'] = put_response.json()['_rev']

        # Get the document again
        response = session.get(
            '{}/{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'document',
                doc_id
            )
        )
        nose.tools.assert_equal(response.status_code, 200)

        # Confirm they are the same, including a matching rev
        nose.tools.assert_equal(doc, response.json())

    def test_get_documents(self):
        cls = type(self)
        session = cls.session

        # Create a document
        response = session.post(
            '{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'documents'
            ),
            json={
                'document': cls.utilities.test_document()
            }
        )
        nose.tools.assert_equal(response.status_code, 201)

        # Create another document
        response = session.post(
            '{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'documents'
            ),
            json={
                'document': cls.utilities.test_document(1)
            }
        )
        nose.tools.assert_equal(response.status_code, 201)

        # Ensure we get just these two documents
        response = session.get(
            '{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'documents'
            )
        )
        nose.tools.assert_equal(response.status_code, 200)

        # Get all the current documents
        docs = response.json()['documents']

        # Ensure they are the correct two documents
        docs = [dict(doc) for doc in docs]
        for doc in docs:
            del doc['_id']
            del doc['_rev']
        docs.remove(cls.utilities.test_document())
        docs.remove(cls.utilities.test_document(1))
        nose.tools.assert_equal(len(docs), 0)
