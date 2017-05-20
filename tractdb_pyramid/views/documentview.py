import cornice
import couchdb.http
import tractdb.server.documents

service_document = cornice.Service(
    name='document',
    path='/document/{id_document}',
    description='TractDB Document',
    cors_origins=('*',),
    cors_credentials=True
)

service_document_collection = cornice.Service(
    name='documents',
    path='/documents',
    description='TractDB Documents Collection',
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


@service_document.get()
def get(request):
    """ Get a document.
    """
    # Our doc_id
    doc_id = request.matchdict['id_document']

    # Our admin object
    admin = _get_admin(request)

    # Be sure it exists
    if not admin.exists_document(doc_id):
        request.response.status_int = 404
        return

    # Get the document
    doc = admin.get_document(doc_id)

    # Return appropriately
    request.response.status_int = 200

    return doc


@service_document.delete()
def delete(request):
    """ Delete a document.
    """
    # Our account parameter
    doc_id = request.matchdict['id_document']

    # Our admin object
    admin = _get_admin(request)

    # Be sure it exists
    if not admin.exists_document(doc_id):
        request.response.status_int = 404
        return

    # Delete it
    admin.delete_document(doc_id)

    # Return appropriately
    request.response.status_int = 200


@service_document_collection.get()
def collection_get(request):
    """ Get a list of documents.
    """
    # Our admin object
    admin = _get_admin(request)

    # Get the document ids
    docs = admin.list_documents()

    # Get the actual documents
    docs = [admin.get_document(doc_id) for doc_id in docs]

    # Return appropriately
    request.response.status_int = 200
    return {
        'documents':
            docs
    }


@service_document_collection.post()
def collection_post(request):
    """ Create an account.
    """

    # Our JSON parameter
    json = request.json_body
    document = json['document']

    # Our admin object
    admin = _get_admin(request)

    # Create the document, a document ID might be specified
    try:
        if 'id' in json:
            doc_id = admin.create_document(
                document,
                doc_id=json['id']
            )
        else:
            doc_id = admin.create_document(
                document
            )
    except couchdb.http.ResourceConflict:
        request.response.status_int = 409
        return

    # Return appropriately
    request.response.status_int = 201
    request.response.headerlist.extend([
        (
            'Location',
            request.route_url('document', id_document=doc_id)
        )
    ])

    return {
        'id': doc_id
    }
