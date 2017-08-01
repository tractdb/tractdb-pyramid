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


@service_document.post()
def post(request):
    """ Create a document.
    """
    # Our doc_id
    doc_id = request.matchdict['id_document']

    # Our JSON parameter
    json = request.json_body
    document = json

    # Our admin object
    admin = _get_admin(request)

    # Create the document with that ID
    try:
        result = admin.create_document(
            document,
            doc_id=doc_id
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
        '_id': doc_id,
        '_rev': result['rev']
    }


@service_document.put()
def put(request):
    """ Create a document, or modify an existing document.
    """
    # Our doc_id
    doc_id = request.matchdict['id_document']

    # TODO: ensure consistent

    # Our JSON parameter
    json = request.json_body
    document = json

    # Our admin object
    admin = _get_admin(request)

    # Create the document with that ID
    try:
        if not admin.exists_document(doc_id):
            result = admin.create_document(
                document,
                doc_id=doc_id
            )

            result_status = 201
        else:
            if not '_rev' in document:
                request.response.status_int = 409
                return

            result = admin.update_document(
                document,
                doc_id=doc_id
            )

            result_status = 200

    except couchdb.http.ResourceConflict:
        request.response.status_int = 409
        return

    # Get our id and our rev
    doc_id = result['id']
    doc_rev = result['rev']

    # Return appropriately
    request.response.status_int = result_status

    return {
        '_id': doc_id,
        '_rev': doc_rev
    }


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
    """ Create a document.
    """

    # Our JSON parameter
    json = request.json_body
    document = json['document']

    # Our admin object
    admin = _get_admin(request)

    # Create the document, a document ID might be specified
    try:
        if 'id' in json:
            result = admin.create_document(
                document,
                doc_id=json['id']
            )
        else:
            result = admin.create_document(
                document
            )
    except couchdb.http.ResourceConflict:
        request.response.status_int = 409
        return

    # Get our id and our rev
    doc_id = result['id']
    doc_rev = result['rev']

    # Return appropriately
    request.response.status_int = 201
    request.response.headerlist.extend([
        (
            'Location',
            request.route_url('document', id_document=doc_id)
        )
    ])

    return {
        '_id': doc_id,
        '_rev': doc_rev
    }
