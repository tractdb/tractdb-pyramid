""" A temporary class containing views for Daniel's storytelling project.
"""

import cornice
import tractdb.server.documents

service_stories = cornice.Service(
    name='storytelling_stories',
    path='/storytelling/stories',
    description='Get all stories associated with the account',
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


@service_stories.get()
def get_stories(request):
    """ Get all stories associated with an account.
    """

    # Our admin object
    admin = _get_admin(request)

    # Get all stories associated with the user
    all_story_docs = [
        admin.get_document(a) for a in admin.list_documents() if a.startswith('story_')
    ]

    # Return appropriately
    request.response.status_int = 200
    return {
        'stories':
            all_story_docs
    }