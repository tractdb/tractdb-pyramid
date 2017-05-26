""" A temporary class containing views for Daniel's storytelling project.
"""

import cornice
import tractdb.server.documents
from stravalib.client import Client as StravaClient
from stravalib import unithelper
from forecastiopy import *
import time

service_runs = cornice.Service(
    name='storytelling_strava_runs',
    path='/storytelling/strava/runs/',
    description='Get all runs associated with the logged in user, provided they have a Strava access token',
    cors_origins=('*',),
    cors_credentials=True
)

service_access_token = cornice.Service(
    name='storytelling_strava_access_token',
    path='/storytelling/strava/access_token/{code}',
    description='Set the access token by exchanging the code provided by Strava',
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

@service_access_token.post()
def set_access_token(request):
    """ Exchange the provided code for an access token and store it
    """

    # Our strava code
    code = request.matchdict['code']

    # If we don't have a strava secret, we can't make the key exchange
    if 'strava' not in request.registry.settings['secrets']:
        request.response.status_int = 500
        return

    # Exchange the code for an access token
    # The API will throw an unspecified error if code is invalid.
    # Catch that rather than taking down the server.
    access_token = ""

    try:
        client = StravaClient()
        access_token = client.exchange_code_for_token(client_id=request.registry.settings['secrets']['strava']['strava_id'],
            client_secret=request.registry.settings['secrets']['strava']['strava_secret'],
            code=code)
    except:
        # Return appropriately
        request.response.status_int = 500
        return

    # Our admin object
    admin = _get_admin(request)

    #Create the access token if it doesn't exist, or update the stored one
    if not admin.exists_document('strava_access_token'):
        # Store the access token
        admin.create_document({'strava_access_token': access_token}, doc_id='strava_access_token')
    else:
        # Update the stored access token
        try:
            admin.update_document({'strava_access_token': access_token, '_id':'strava_access_token'})
        except:
            # By design, "update" seems to throw an exception? Not really sure why.
            # But return correctly if it worked.
            request.response.status_int = 200
            return {
                'access_token':
                    access_token
            }
        

    # Return appropriately
    request.response.status_int = 200
    return {
        'access_token':
            access_token
    }
    


@service_runs.get()
def get_runs(request):
    """ Get all runs associated with an account.
    """

    # Our admin object
    admin = _get_admin(request)

    # Be sure it exists
    if not admin.exists_document('strava_access_token'):
        request.response.status_int = 403
        return

    # Get the access token
    access_token = admin.get_document('strava_access_token')

    running_docs = {
        a:admin.get_document(a) for a in admin.list_documents() if a.startswith('run_')
    }

    strava_client = StravaClient(access_token=access_token['strava_access_token'])

    runs = []
    for a in strava_client.get_activities():
        if 'run_' + str(a.id) in running_docs:
            run = running_docs['run_' + str(a.id)]
        else:
            run = {
                'id': a.id,
                'timestamp': a.start_date_local.isoformat(),
                'duration': a.elapsed_time.total_seconds(),
                'distance': unithelper.miles(a.distance).num,
                'name': a.name,
                'description': a.description
            }
            if a.map.summary_polyline is not None:
                run['map_polyline'] = a.map.summary_polyline
            if a.start_latlng is not None and a.start_date is not None and 'darksky' in request.registry.settings['secrets']:
                fio = ForecastIO.ForecastIO(
                    request.registry.settings['secrets']['darksky']['darksky_secret'],
                    units=ForecastIO.ForecastIO.UNITS_US,
                    latitude=float(a.start_latlng[0]),
                    longitude=float(a.start_latlng[1]),
                    time=str(int(time.mktime(a.start_date.timetuple())))
                )
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
