import cornice
import tractdb.server.documents
from stravalib.client import Client as StravaClient
from stravalib import unithelper

service_runs = cornice.Service(
    name='storytelling_strava_runs',
    path='/storytelling_strava/runs/{id_account}',
    description='Get all runs associated with an account id',
    cors_origins=('*',),
    cors_credentials=True
)

service_access = cornice.Service(
    name='storytelling_strava_access',
    path='/storytelling_strava/access_token/{id_account}',
    description='Get or set the access token associated with an account',
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

@service_runs.get()
def get_runs(request):
    """ Get all runs associated with an account.
    """

    # Our account parameter
    account_id = request.matchdict['id_account']

    # Our admin object
    admin = _get_admin(request)

    # Be sure it exists
    if not admin.exists_document(account_id):
        request.response.status_int = 404
        return

    # Get the document
    account_doc = admin.get_document(account_id)


    # Make sure there's a Strava access token
    if not 'strava_access_token' in account_doc:
        request.response.status_int = 404
        return

    strava_client = StravaClient(access_token=account_doc['strava_access_token'])
    
    runs = []
    for a in strava_client.get_activities():
        if a.map.summary_polyline is not None:
            runs.append({'id':a.id, 'timestamp':a.start_date_local.isoformat(), 'duration':a.elapsed_time.total_seconds(), 'map_polyline':a.map.summary_polyline, 'distance':unithelper.miles(a.distance).num})

    # Return appropriately
    request.response.status_int = 200
    return {
        'runs':
            runs
    }

@service_access.get()
def get_access_token(request):
    """ Gets whether there's an access token associated with this account.
    """

    # Our account parameter
    account_id = request.matchdict['id_account']

    # Our admin object
    admin = _get_admin(request)

    # Be sure it exists
    if not admin.exists_document(account_id):
        request.response.status_int = 404
        return

    # Get the document
    account_doc = admin.get_document(account_id)

    # Return appropriately
    if not 'strava_access_token' in account_doc:
        request.response.status_int = 404
        return

    request.response.status_int = 200
    return

@service_access.post()
def set_access_token(request):
    """ Set the access token associated with an account.
    """

    # Our account parameter
    account_id = request.matchdict['id_account']

    # Our JSON parameter
    json = request.json_body

    # Be sure the strava token exists
    if not 'strava_access_token' in json:
        request.response.status_int = 404
        return

    access_token = json['strava_access_token']

    # Our admin object
    admin = _get_admin(request)

    # Create the document
    doc_id = admin.create_document(
        {'strava_access_token': access_token},
        doc_id=account_id
    )

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