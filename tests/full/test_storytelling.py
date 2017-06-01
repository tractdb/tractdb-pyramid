'''A temporary test class for Daniel's storytelling project'''

import nose.tools
import tests.utilities

class TestStorytelling:
    @classmethod
    def setup_class(cls):
        cls.utilities = tests.utilities.Utilities('TestStorytelling')

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

    @nose.tools.nottest
    def get_story_document_id(self, story_id=0):
        return 'st_{}'.format(story_id)

    @nose.tools.nottest
    def get_story_document(self, story_id=0, storyType='diy', storyTitle='test_story'):
        return {
            'storyType':storyType,
            'storyTitle':'{}_{}'.format(
                storyTitle,
                story_id)
        }

    @nose.tools.nottest
    def get_chapter_document_id(self, chapter_id=0):
        return 'ch_{}'.format(chapter_id)

    @nose.tools.nottest
    def get_chapter_document(self, chapter_id=0, story_id=0):
        return {
            'id': 'ch_{}'.format(chapter_id),
            'storyId': 'st_{}'.format(story_id),
            'data': {
                'chapterData': 'test_{}'.format(chapter_id)
            }
        }

    def test_create_story_and_get_stories(self):
        cls = type(self)
        session = cls.session

        # Create a story with a particular id
        response_post = session.post(
            '{}/{}/story_{}'.format(
                cls.utilities.url_base_pyramid(),
                'document',
                self.get_story_document_id(1)
            ),
            json=self.get_story_document(1)
        )
        nose.tools.assert_equal(response_post.status_code, 201)

        # Create another story with a particular id
        response_post = session.post(
            '{}/{}/story_{}'.format(
                cls.utilities.url_base_pyramid(),
                'document',
                self.get_story_document_id(2)
            ),
            json=self.get_story_document(story_id=2, storyType='running')
        )
        nose.tools.assert_equal(response_post.status_code, 201)

        # Create a chapter, which is not a story
        response_post = session.post(
            '{}/{}/chapter_{}'.format(
                cls.utilities.url_base_pyramid(),
                'document',
                self.get_chapter_document_id(1)
            ),
            json=self.get_chapter_document(chapter_id=1, story_id=1)
        )
        nose.tools.assert_equal(response_post.status_code, 201)

        # Call get_stories, ensure we get only the two stories
        response = session.get(
            '{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'storytelling/stories'
            )
        )
        nose.tools.assert_equal(response.status_code, 200)

        # Get all the stories
        docs = response.json()['stories']

        # Ensure they are the correct two stories
        docs = [dict(doc) for doc in docs]
        for doc in docs:
            del doc['_id']
            del doc['_rev']
        docs.remove(self.get_story_document(story_id=1))
        docs.remove(self.get_story_document(story_id=2, storyType='running'))
        nose.tools.assert_equal(len(docs), 0)

    def test_get_chapters(self):
        cls = type(self)
        session = cls.session

        # Create a story with a particular id
        response_post = session.post(
            '{}/{}/story_{}'.format(
                cls.utilities.url_base_pyramid(),
                'document',
                self.get_story_document_id(1)
            ),
            json=self.get_story_document(story_id=1)
        )
        nose.tools.assert_equal(response_post.status_code, 201)

        # Create another story with a particular id
        response_post = session.post(
            '{}/{}/story_{}'.format(
                cls.utilities.url_base_pyramid(),
                'document',
                self.get_story_document_id(story_id=2)
            ),
            json=self.get_story_document(story_id=2, storyType='running')
        )
        nose.tools.assert_equal(response_post.status_code, 201)

        # Create a chapter part of story 1
        response_post = session.post(
            '{}/{}/chapter_{}'.format(
                cls.utilities.url_base_pyramid(),
                'document',
                self.get_chapter_document_id(1)
            ),
            json=self.get_chapter_document(chapter_id=1, story_id=1)
        )
        nose.tools.assert_equal(response_post.status_code, 201)

        # Create another chapter part of story 1
        response_post = session.post(
            '{}/{}/chapter_{}'.format(
                cls.utilities.url_base_pyramid(),
                'document',
                self.get_chapter_document_id(2)
            ),
            json=self.get_chapter_document(chapter_id=2, story_id=1)
        )
        nose.tools.assert_equal(response_post.status_code, 201)

        # Create a chapter not part of story 1
        response_post = session.post(
            '{}/{}/chapter_{}'.format(
                cls.utilities.url_base_pyramid(),
                'document',
                self.get_chapter_document_id(3)
            ),
            json=self.get_chapter_document(chapter_id=3, story_id=2)
        )
        nose.tools.assert_equal(response_post.status_code, 201)

        # Call get_chapters on the first story, ensure we get only the two chapters
        response = session.get(
            '{}/{}/{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'storytelling',
                self.get_story_document_id(1),
                'chapters'
            )
        )
        nose.tools.assert_equal(response.status_code, 200)

        # Get all the chapters
        docs = response.json()['chapters']

        # Ensure they are the correct two chapters
        docs = [dict(doc) for doc in docs]
        for doc in docs:
            del doc['_id']
            del doc['_rev']
        docs.remove(self.get_chapter_document(chapter_id=1, story_id=1))
        docs.remove(self.get_chapter_document(chapter_id=2, story_id=1))
        nose.tools.assert_equal(len(docs), 0)

        # Call get_chapters on the second story, ensure we get only the third chapter
        response = session.get(
            '{}/{}/{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'storytelling',
                self.get_story_document_id(2),
                'chapters'
            )
        )
        nose.tools.assert_equal(response.status_code, 200)

        # Get all the chapters
        docs = response.json()['chapters']

        # Ensure it is the correct chapter
        docs = [dict(doc) for doc in docs]
        for doc in docs:
            del doc['_id']
            del doc['_rev']
        docs.remove(self.get_chapter_document(chapter_id=3, story_id=2))
        nose.tools.assert_equal(len(docs), 0)

    def test_add_delete_chapters(self):
        cls = type(self)
        session = cls.session

        # Create a story with a particular id
        response_post = session.post(
            '{}/{}/story_{}'.format(
                cls.utilities.url_base_pyramid(),
                'document',
                self.get_story_document_id(1)
            ),
            json=self.get_story_document(1)
        )
        nose.tools.assert_equal(response_post.status_code, 201)

        # Create a chapter part of the story
        response_post = session.post(
            '{}/{}/chapter_{}'.format(
                cls.utilities.url_base_pyramid(),
                'document',
                self.get_chapter_document_id(1)
            ),
            json=self.get_chapter_document(chapter_id=1, story_id=1)
        )
        nose.tools.assert_equal(response_post.status_code, 201)

        # Create another chapter part the story
        response_post = session.post(
            '{}/{}/chapter_{}'.format(
                cls.utilities.url_base_pyramid(),
                'document',
                self.get_chapter_document_id(2)
            ),
            json=self.get_chapter_document(chapter_id=2, story_id=1)
        )
        nose.tools.assert_equal(response_post.status_code, 201)

        # Call get_chapters on the story, ensure we get the two chapters
        response = session.get(
            '{}/{}/{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'storytelling',
                self.get_story_document_id(1),
                'chapters'
            )
        )
        nose.tools.assert_equal(response.status_code, 200)

        # Get all the chapters
        docs = response.json()['chapters']

        # Ensure they are the correct two chapters
        docs = [dict(doc) for doc in docs]
        for doc in docs:
            del doc['_id']
            del doc['_rev']
        docs.remove(self.get_chapter_document(chapter_id=1, story_id=1))
        docs.remove(self.get_chapter_document(chapter_id=2, story_id=1))
        nose.tools.assert_equal(len(docs), 0)

        # Delete one of the chapters
        response_delete = session.delete(
            '{}/{}/chapter_{}'.format(
                cls.utilities.url_base_pyramid(),
                'document',
                self.get_chapter_document_id(1)
            )
        )
        nose.tools.assert_equal(response_delete.status_code, 200)

        # Call get_chapters on the story, ensure we now only have one chapter
        response = session.get(
            '{}/{}/{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'storytelling',
                self.get_story_document_id(1),
                'chapters'
            )
        )
        nose.tools.assert_equal(response.status_code, 200)

        # Get all the chapters
        docs = response.json()['chapters']

        # Ensure it is the correct chapter
        docs = [dict(doc) for doc in docs]
        for doc in docs:
            del doc['_id']
            del doc['_rev']
        docs.remove(self.get_chapter_document(chapter_id=2, story_id=1))
        nose.tools.assert_equal(len(docs), 0)