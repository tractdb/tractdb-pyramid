import base64
import cornice
import pyramid.security
import requests
import tractdb.server.documents


def acl_authenticated(request):
    return [
        (pyramid.security.Allow, pyramid.security.Authenticated, 'authenticated'),
        pyramid.security.DENY_ALL
    ]


service_configure_fitbit = cornice.Service(
    name='configure fitbit',
    path='/configure/fitbit/callback_code',
    description='Configure Fitbit Callback Code',
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


@service_configure_fitbit.post(permission='authenticated')
def post(request):
    """ Receive a Fitbit authentication code, convert it into a token.
    """
    # Our admin object
    admin = _get_admin(request)

    # Need a Fitbit secret to make the exchange
    secrets_fitbit = request.registry.settings['secrets'].get('fitbit', None)
    if secrets_fitbit is None:
        request.response.status_int = 500
        return

    # The code provided in response to an authentication
    callback_code = request.json_body['callback_code']

    # Get a token from Fitbit
    response = requests.post(
        'https://api.fitbit.com/oauth2/token',
        headers={
            'Authorization':
                'Basic {}'.format(
                    base64.b64encode('{}:{}'.format(
                        secrets_fitbit['fitbit_id'],
                        secrets_fitbit['fitbit_secret']
                    ).encode('utf-8')).decode('utf-8')
                )
        },
        data={
            'grant_type': 'authorization_code',
            'client_id': secrets_fitbit['fitbit_id'],
            'code': callback_code,
            'redirect_uri': secrets_fitbit['fitbit_redirect_uri']
        }
    )

    # Ensure we got our response
    if response.status_code != 200:
        request.response.status_int = 502
        return

    # Our current token
    new_token = response.json()

    # Store according to its 'user_id', which allows multiple Fitbit accounts per TractDB account
    if admin.exists_document('fitbit_tokens'):
        doc_tokens = admin.get_document('fitbit_tokens')
    else:
        doc_tokens = {
            'fitbit_tokens': []
        }

    # A list of tokens will be stored
    stored_tokens = doc_tokens['fitbit_tokens']

    # Update that list
    stored_tokens = [old_token for old_token in stored_tokens if old_token['user_id'] != new_token['user_id']]
    stored_tokens.append(new_token)
    doc_tokens['fitbit_tokens'] = stored_tokens

    # Store the updated document
    if admin.exists_document('fitbit_tokens'):
        admin.update_document(doc_tokens)
    else:
        admin.create_document(doc_tokens, doc_id='fitbit_tokens')

    request.response.status_int = 200
