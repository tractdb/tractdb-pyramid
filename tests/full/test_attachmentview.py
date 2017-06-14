import nose.tools
import tests.utilities


class TestAttachmentView:
    @classmethod
    def setup_class(cls):
        cls.utilities = tests.utilities.Utilities('TestAttachmentView')

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
        session = cls.session

        # Ensure no documents remain from prior tests
        cls.utilities.delete_all_documents(cls.session)

        # Create a test document on which we'll manipulate attachments
        response_post = session.post(
            '{}/{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'document',
                cls.utilities.test_document_id()
            ),
            json=cls.utilities.test_document()
        )
        nose.tools.assert_equal(response_post.status_code, 201)

    def teardown(self):
        cls = type(self)

        # Clean up our documents
        cls.utilities.delete_all_documents(cls.session)

    def test_create_get_modify_delete_attachment(self):
        cls = type(self)
        session = cls.session

        # We need the initial _rev of the document
        response = session.get(
            '{}/{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'document',
                cls.utilities.test_document_id()
            )
        )
        nose.tools.assert_equal(response.status_code, 200)
        doc = response.json()

        # Manipulate these throughout test
        doc_id = doc['_id']
        doc_rev = doc['_rev']

        # Create an attachment
        response = session.post(
            '{}/{}/{}/{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'document',
                doc_id,
                'attachment',
                cls.utilities.test_attachment_name()
            ),
            params={
                'rev': doc_rev
            },
            headers={
                'Content-Type': 'image/png'
            },
            data=cls.utilities.test_image_bytes()
        )
        nose.tools.assert_equal(response.status_code, 201)

        # Confirm it appears in the list of attachments
        response = session.get(
            '{}/{}/{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'document',
                doc_id,
                'attachments'
            )
        )
        nose.tools.assert_equal(response.status_code, 200)
        nose.tools.assert_in(
            cls.utilities.test_attachment_name(),
            response.json()['attachments']
        )

        # Get the attachment
        response = session.get(
            '{}/{}/{}/{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'document',
                doc_id,
                'attachment',
                cls.utilities.test_attachment_name()
            )
        )
        nose.tools.assert_equal(response.status_code, 200)

        # Confirm the content matches
        nose.tools.assert_equal(
            response.headers['Content-Type'],
            'image/png'
        )
        nose.tools.assert_equal(
            response.content,
            cls.utilities.test_image_bytes()
        )

        # Modify it
        response = session.put(
            '{}/{}/{}/{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'document',
                doc_id,
                'attachment',
                cls.utilities.test_attachment_name()
            ),
            params={
                'rev': doc_rev
            },
            headers={
                'Content-Type': 'image/png'
            },
            data=cls.utilities.test_image_bytes(1)
        )
        nose.tools.assert_equal(response.status_code, 200)

        # Get the attachment again
        response = session.get(
            '{}/{}/{}/{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'document',
                doc_id,
                'attachment',
                cls.utilities.test_attachment_name()
            )
        )
        nose.tools.assert_equal(response.status_code, 200)

        # Confirm the modification happened
        nose.tools.assert_not_equal(
            response.content,
            cls.utilities.test_image_bytes()
        )

        # Confirm the modification happened
        nose.tools.assert_equal(
            response.content,
            cls.utilities.test_image_bytes(1)
        )

        # Delete the attachment
        response = session.delete(
            '{}/{}/{}/{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'document',
                doc_id,
                'attachment',
                cls.utilities.test_attachment_name()
            ),
            params={
                'rev': doc_rev
            }
        )
        nose.tools.assert_equal(response.status_code, 200)

        # Confirm that getting it fails
        response = session.get(
            '{}/{}/{}/{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'document',
                doc_id,
                'attachment',
                cls.utilities.test_attachment_name()
            )
        )
        nose.tools.assert_equal(response.status_code, 404)

        # Confirm it is no longer in the list of attachments
        response = session.get(
            '{}/{}/{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'document',
                doc_id,
                'attachments'
            )
        )
        nose.tools.assert_equal(response.status_code, 200)
        nose.tools.assert_not_in(
            cls.utilities.test_attachment_name(),
            response.json()['attachments']
        )
