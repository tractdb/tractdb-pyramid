import cornice
import tractdb.server.documents
from stravalib.client import Client as StravaClient
from stravalib import unithelper
from forecastiopy import *
import time

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

    # Our admin object
    admin = _get_admin(request)

    # Be sure it exists
    if not admin.exists_document('strava_access_token'):
        request.response.status_int = 404
        return

    # Get the access token
    access_token = admin.get_document('strava_access_token')


    if 'strava_access_token' not in access_token:
        request.response.status_int = 404
        return

    running_docs = {a:admin.get_document(a) for a in admin.list_documents() if a.startswith('run_')}

    strava_client = StravaClient(access_token=access_token['strava_access_token'])


    
    runs = []
    for a in strava_client.get_activities():
        if 'run_' + str(a.id) in running_docs:
            run = running_docs['run_' + str(a.id)]
        else:
            run = {'id':a.id, 'timestamp':a.start_date_local.isoformat(), 'duration':a.elapsed_time.total_seconds(), 'distance':unithelper.miles(a.distance).num, 'name':a.name, 'description':a.description}
            if a.map.summary_polyline is not None:
                run['map_polyline'] = a.map.summary_polyline
            if a.start_latlng is not None and a.start_date is not None:
                fio = ForecastIO.ForecastIO(request.registry.settings['darksky_secrets']['darksky_secret'], units=ForecastIO.ForecastIO.UNITS_US, latitude=float(a.start_latlng[0]), longitude=float(a.start_latlng[1]), time=str(int(time.mktime(a.start_date.timetuple()))))
                if fio.has_currently():
                    currently = FIOCurrently.FIOCurrently(fio)
                    run['temperature'] = currently.temperature
                    run['weather_icon'] = currently.icon
            admin.create_document(run, doc_id='run_' + str(a.id))
        runs.append(run)

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

    # Our admin object
    admin = _get_admin(request)

    # Be sure it exists
    if not admin.exists_document('strava_access_token'):
        request.response.status_int = 404
        return

    request.response.status_int = 200
    return

@service_access.post()
def set_access_token(request):
    """ Set the access token associated with an account.
    """

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
        doc_id='strava_access_token'
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