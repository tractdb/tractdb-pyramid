""" A temporary class containing views for Daniel's storytelling project.
"""

import cornice
import tractdb.server.documents

service_chapters = cornice.Service(
    name='storytelling_chapters',
    path='/storytelling/chapters',
    description='Get all chapters associated with the logged in user',
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
    """ Get all public chapters associated with an account.
    """

    # Our admin object
    admin = _get_admin(request)

    # Get all chapters
    all_chapter_docs = [
        admin.get_document(a) for a in admin.list_documents() if a.startswith('chapter_')
    ]

    # Return appropriately
    request.response.status_int = 200
    return {
        'chapters':
            all_chapter_docs
    }