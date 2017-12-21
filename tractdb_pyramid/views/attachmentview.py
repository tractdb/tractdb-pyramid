import cornice
import couchdb.http
import pyramid.security
import tractdb.server.documents


def acl_authenticated(request):
    return [
        (pyramid.security.Allow, pyramid.security.Authenticated, 'authenticated'),
        pyramid.security.DENY_ALL
    ]


service_attachment = cornice.Service(
    name='attachment',
    path='/document/{id_document}/attachment/{id_attachment}',
    description='TractDB Attachment',
    cors_origins=('*',),
    cors_credentials=True,
    acl=acl_authenticated
)

service_attachment_collection = cornice.Service(
    name='attachments',
    path='/document/{id_document}/attachments',
    description='TractDB Attachments Collection',
    cors_origins=('*',),
    cors_credentials=True,
    acl=acl_authenticated
)


def _get_admin(request):
    # Create our admin object
    admin = tractdb.server.documents.DocumentsAdmin(
        couchdb_url=request.registry.settings['tractdb_couchdb'],
        couchdb_user=request.session['temp_couchdb_user'],
        couchdb_user_password=request.session['temp_couchdb_user_password']
    )

    return admin


@service_attachment.delete(permission='authenticated')
def delete(request):
    """ Delete an attachment.
    """
    # Our doc_id and attachment name
    doc_id = request.matchdict['id_document']
    attachment_name = request.matchdict['id_attachment']

    # Our admin object
    admin = _get_admin(request)

    # Get the document
    doc = admin.get_document(doc_id)

    if attachment_name not in doc.get('_attachments', []):
        request.response.status_int = 404
        return

    # Delete it
    admin.delete_attachment(doc_id, attachment_name)

    # Return appropriately
    request.response.status_int = 200


@service_attachment.get(permission='authenticated')
def get(request):
    """ Get an attachment.
    """
    # Our doc_id and attachment name
    doc_id = request.matchdict['id_document']
    attachment_name = request.matchdict['id_attachment']

    # Our admin object
    admin = _get_admin(request)

    # Get the document
    doc = admin.get_document(doc_id)

    if attachment_name not in doc.get('_attachments', []):
        request.response.status_int = 404
        return

    # Get the attachment
    result = admin.get_attachment(doc_id, attachment_name)

    # Return appropriately
    request.response.status_int = 200
    request.response.content_type = result['content_type']
    request.response.body = result['content'].read()
    result['content'].close()

    return request.response


@service_attachment.post(permission='authenticated')
def post(request):
    """ Create an attachment on a document.
    """
    # Our doc_id and attachment name
    doc_id = request.matchdict['id_document']
    attachment_name = request.matchdict['id_attachment']

    # Attachment bytes and type
    attachment_bytes = request.body
    attachment_content_type = request.headers['Content-Type']

    # Our admin object
    admin = _get_admin(request)

    # Get the document
    doc = admin.get_document(doc_id)

    # Create the attachment with that name
    try:
        if attachment_name in doc.get('_attachments', []):
            request.response.status_int = 409
            return

        result = admin.create_attachment(
            doc,
            attachment_name,
            attachment_bytes,
            content_type=attachment_content_type
        )
    except couchdb.http.ResourceConflict:
        request.response.status_int = 409
        return

    # Return appropriately
    request.response.status_int = 201

    return {
        '_id': doc_id,
        '_rev': result['rev']
    }


@service_attachment.put(permission='authenticated')
def put(request):
    """ Modify an existing attachment on a document.
    """
    # Our doc_id and attachment name
    doc_id = request.matchdict['id_document']
    attachment_name = request.matchdict['id_attachment']

    # Attachment bytes and type
    attachment_bytes = request.body
    attachment_content_type = request.headers['Content-Type']

    # Our admin object
    admin = _get_admin(request)

    # Get the document
    doc = admin.get_document(doc_id)

    # Create the attachment with that name
    try:
        result = admin.create_attachment(
            doc,
            attachment_name,
            attachment_bytes,
            content_type=attachment_content_type
        )
    except couchdb.http.ResourceConflict:
        request.response.status_int = 409
        return

    # Return appropriately
    request.response.status_int = 200

    return {
        '_id': doc_id,
        '_rev': result['rev']
    }


@service_attachment_collection.get(permission='authenticated')
def collection_get(request):
    """ Get a list of attachments on a document.
    """
    # Our doc_id and attachment name
    doc_id = request.matchdict['id_document']

    # Our admin object
    admin = _get_admin(request)

    # Get the document
    doc = admin.get_document(doc_id)

    # Get the attachment list
    attachments = doc.get('_attachments', [])

    # Return appropriately
    request.response.status_int = 200
    return {
        'attachments':
            attachments
    }
