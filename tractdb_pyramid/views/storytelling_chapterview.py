""" A temporary class containing views for Daniel's storytelling project.
"""

import cornice
import tractdb.server.documents

service_chapters = cornice.Service(
    name='storytelling_chapters',
    path='/storytelling/{story_id}/chapters',
    description='Get all chapters associated with a story',
    cors_origins=('*',),
    cors_credentials=True
)


def _get_admin(request):
    # Create our admin object
    admin = tractdb.server.documents.DocumentsAdmin(
        couchdb_url=request.registry.settings['tractdb_couchdb'],
        couchdb_user=request.session['temp_couchdb_user'],
        couchdb_user_password=request.session['temp_couchdb_user_password']
    )

    return admin


@service_chapters.get()
def get_chapters(request):
    """ Get all chapters associated with a story.
    """

    # Our story id
    story_id = request.matchdict['story_id']

    # Our admin object
    admin = _get_admin(request)

    # Be sure the story exists
    if not admin.exists_document('story_' + story_id):
        request.response.status_int = 404
        return

    # Get all chapters associated with the user
    all_chapter_docs = [
        admin.get_document(a) for a in admin.list_documents() if a.startswith('chapter_')
    ]

    # Filter to chapters associated with the story
    story_chapter_docs = [
        c for c in all_chapter_docs if 'storyId' in c and c['storyId'] == story_id
    ]

    # Return appropriately
    request.response.status_int = 200
    return {
        'chapters':
            story_chapter_docs
    }