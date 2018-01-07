""" A temporary class containing views for Daniel's storytelling project.
"""

import cornice
import tractdb.server.documents

service_allchapters = cornice.Service(
    name='storytelling_allchapters',
    path='/storytelling/chapters',
    description='Get all chapters associated with the account',
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


@service_allchapters.get()
def get_chapters(request):
    """ Get all chapters associated with an account.
    """

    # Our admin object
    admin = _get_admin(request)

    # Get all chapters associated with the user
    all_chapter_docs = [
        admin.get_document(a) for a in admin.list_documents() if a.startswith('chapter_')
    ]

    # Return appropriately
    request.response.status_int = 200
    return {
        'chapters':
            all_chapter_docs
    }