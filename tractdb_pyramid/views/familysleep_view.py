import base64
import cornice
import datetime
import pyramid.security
import requests
import tractdb.server.documents


def acl_authenticated(request):
    return [
        (pyramid.security.Allow, pyramid.security.Authenticated, 'authenticated'),
        pyramid.security.DENY_ALL
    ]


service_fitbitquery = cornice.Service(
    name='familysleep_fitbitquery',
    path='/familysleep/fitbitquery',
    description='Get Fitbit sleep data for known devices',
    cors_origins=('*',),
    cors_credentials=True,
    acl=acl_authenticated
)

service_family_daily = cornice.Service(
    name='familysleep_familydaily',
    path='/familysleep/familydaily/{date}',
    description='Get data for a family for a single day',
    cors_origins=('*',),
    cors_credentials=True,
    acl=acl_authenticated
)

service_family_weekly = cornice.Service(
    name='familysleep_familyweekly',
    path='/familysleep/familyweekly/{date}',
    description='Get data for a family for a week',
    cors_origins=('*',),
    cors_credentials=True,
    acl=acl_authenticated
)

service_single_daily = cornice.Service(
    name='familysleep_singledaily',
    path='/familysleep/singledaily/{pid}/{date}',
    description='Get data for a single person for a single day',
    cors_origins=('*',),
    cors_credentials=True,
    acl=acl_authenticated
)

service_single_weekly = cornice.Service(
    name='familysleep_singleweekly',
    path='/familysleep/singleweekly/{pid}/{date}',
    description='Get data for a single person for a week',
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


def _prepare_content_empty_day_sleep(*, docs, pid, date):
    doc_persona = docs['familysleep_personas']['personas'][pid]

    doc_result = {}

    # Populate default fields
    doc_result['pid'] = pid
    doc_result['name'] = doc_persona['name']
    doc_result['dateOfSleep'] = date

    # Initially we have no sleep document
    doc_result['fid'] = ''
    doc_result['duration'] = -1
    doc_result['startTime'] = -1
    doc_result['endTime'] = -1

    return doc_result


def _compute_minutes_chart_data(*, fitbit_minute_data, time_start=datetime.time(hour=17), time_end=datetime.time(hour=8)):
    # Determine how 'long' our chart data is
    number_minutes_to_plot = (
        datetime.datetime.combine(datetime.date.min + datetime.timedelta(days=1), time_end) -
        datetime.datetime.combine(datetime.date.min, time_start)
    ).total_seconds() / 60
    number_minutes_to_plot = int(number_minutes_to_plot)

    # Determine how many minutes we plot before midnight
    number_minutes_plotted_before_midnight = (
        datetime.datetime.combine(datetime.date.min + datetime.timedelta(days=1), datetime.time()) -
        datetime.datetime.combine(datetime.date.min, time_start)
    ).total_seconds() / 60
    number_minutes_plotted_before_midnight = int(number_minutes_plotted_before_midnight)

    # Iterate over these to populate our minutes chart data
    minutes_chart_data = {}
    sleep_values = [
        (1, 'one'),
        (2, 'two'),
        (3, 'three')
    ]
    for current_sleep_value, current_sleep_value_text in sleep_values:
        # Create a list of '0' that is the correct length, change the values that matter
        current_sleep_chart_data = [0] * number_minutes_to_plot

        # Go through all the values
        for current_fitbit_minute_entry in fitbit_minute_data:
            current_fitbit_minute = current_fitbit_minute_entry['dateTime']
            current_fitbit_value = int(current_fitbit_minute_entry['value'])

            if current_fitbit_value == current_sleep_value:
                parsed_hour = int(current_fitbit_minute.split(':')[0])
                parsed_minute = int(current_fitbit_minute.split(':')[1])

                if datetime.time(hour=parsed_hour, minute=parsed_minute) > time_start:
                    # it's not yet midnight, so our index is the time since start
                    current_minute_index = (
                        datetime.datetime.combine(datetime.date.min, datetime.time(hour=parsed_hour, minute=parsed_minute)) -
                        datetime.datetime.combine(datetime.date.min, time_start)
                    ).total_seconds() / 60
                    current_minute_index = int(current_minute_index)
                else:
                    # it's after minute, so our index is the entire prior day plus time since midnight
                    current_minute_index = (
                        number_minutes_plotted_before_midnight +
                        parsed_hour * 60 +
                        parsed_minute
                    )

                if current_minute_index >= 0 and current_minute_index < number_minutes_to_plot:
                    current_sleep_chart_data[current_minute_index] = 3  # magic value used by plotting

        minutes_chart_data[current_sleep_value_text] = current_sleep_chart_data

    # Compute a label for each bucket
    minutes_chart_data['labels'] = [
        (
            datetime.datetime.combine(datetime.date.min, time_start) + datetime.timedelta(minutes=current_minute)
        ).strftime('%I:%M %p')
        for current_minute
        in range(0, number_minutes_to_plot)
    ]

    return minutes_chart_data


def _compute_family_daily(*, docs, date):
    doc_personas = docs['familysleep_personas']

    doc_result = {}
    for current_pid in doc_personas['personas'].keys():
        # Results for this pid
        doc_result[current_pid] = {}

        # Get the single_daily doc
        doc_single_daily = _compute_single_daily(
            docs=docs,
            pid=current_pid,
            date=date,
            with_chart_data=False
        )

        # Get its inner content, return it for ourselves
        doc_result[current_pid][date] = doc_single_daily[current_pid][date]

    return doc_result


def _compute_family_weekly(*, docs, date):
    doc_personas = docs['familysleep_personas']

    doc_result = {}
    for current_pid in doc_personas['personas'].keys():
        # Results for this pid
        doc_result[current_pid] = {}

        for days_back in reversed(range(0, 7)):
            current_date = datetime.datetime.strptime(date, '%Y-%m-%d') - datetime.timedelta(days=days_back)
            current_date = current_date.strftime('%Y-%m-%d')

            # Get the single_daily doc
            doc_single_daily = _compute_single_daily(
                docs=docs,
                pid=current_pid,
                date=current_date,
                with_chart_data=False
            )

            # Get its inner content, return it for ourselves
            doc_result[current_pid][current_date] = doc_single_daily[current_pid][current_date]

    return doc_result


def _compute_single_daily(*, docs, pid, date, with_chart_data):
    doc_persona = docs['familysleep_personas']['personas'][pid]

    # Start with empty sleep data
    doc_content = _prepare_content_empty_day_sleep(docs=docs, pid=pid, date=date)

    # Find the Fitbit sleep document for the day
    doc_id_fitbit_sleep = 'fitbit-{}-sleep-{}'.format(
        doc_persona['fitbit'],
        date
    )
    if doc_id_fitbit_sleep in docs:
        doc_fitbit_sleep = docs[doc_id_fitbit_sleep]

        # Directly copy some fields from that
        doc_content['fid'] = doc_fitbit_sleep['logId']
        doc_content['duration'] = doc_fitbit_sleep['duration']
        doc_content['startTime'] = doc_fitbit_sleep['startTime']
        doc_content['endTime'] = doc_fitbit_sleep['endTime']

        if with_chart_data:
            # Compute the chart data
            minutes_chart_data = _compute_minutes_chart_data(fitbit_minute_data=doc_fitbit_sleep['minuteData'])
            doc_content['minuteData'] = minutes_chart_data

    # Nest it within appropriate keys
    return {
        pid: {
            date: doc_content
        }
    }


def _compute_single_weekly(*, docs, pid, date, with_chart_data):
    doc_personas = docs['familysleep_personas']

    doc_result = {}
    doc_result[pid] = {}

    for days_back in reversed(range(0, 7)):
        current_date = datetime.datetime.strptime(date, '%Y-%m-%d') - datetime.timedelta(days=days_back)
        current_date = current_date.strftime('%Y-%m-%d')

        # Get the single_daily doc
        doc_single_daily = _compute_single_daily(
            docs=docs,
            pid=pid,
            date=current_date,
            with_chart_data=with_chart_data
        )

        # Get its inner content, return it for ourselves
        doc_result[pid][current_date] = doc_single_daily[pid][current_date]

    return doc_result


@service_family_daily.get(permission='authenticated')
def service_family_daily_get(request):
    _fitbitquery(request)

    # Parameters
    date = request.matchdict['date']

    # Admin object
    admin = _get_admin(request)

    # Gather the documents it will need
    docs = {}
    docs['familysleep_personas'] = admin.get_document(doc_id='familysleep_personas')
    for current_pid in docs['familysleep_personas']['personas'].keys():
        doc_id_fitbit_sleep = 'fitbit-{}-sleep-{}'.format(
            docs['familysleep_personas']['personas'][current_pid]['fitbit'],
            date
        )

        if admin.exists_document(doc_id=doc_id_fitbit_sleep):
            docs[doc_id_fitbit_sleep] = admin.get_document(doc_id_fitbit_sleep)

    # Compute the summary
    doc_result = _compute_family_daily(docs=docs, date=date)

    # Return appropriately
    request.response.status_int = 200

    return doc_result


@service_family_weekly.get(permission='authenticated')
def service_family_weekly_get(request):
    _fitbitquery(request)

    # Parameters
    date = request.matchdict['date']

    # Admin object
    admin = _get_admin(request)

    # Gather the documents it will need
    docs = {}
    docs['familysleep_personas'] = admin.get_document(doc_id='familysleep_personas')

    for current_pid in docs['familysleep_personas']['personas'].keys():
        for days_back in reversed(range(0, 7)):
            current_date = datetime.datetime.strptime(date, '%Y-%m-%d') - datetime.timedelta(days=days_back)
            current_date = current_date.strftime('%Y-%m-%d')

            doc_id_fitbit_sleep = 'fitbit-{}-sleep-{}'.format(
                docs['familysleep_personas']['personas'][current_pid]['fitbit'],
                current_date
            )
            if admin.exists_document(doc_id=doc_id_fitbit_sleep):
                docs[doc_id_fitbit_sleep] = admin.get_document(doc_id_fitbit_sleep)

    # Compute the summary
    doc_result = _compute_family_weekly(docs=docs, date=date)

    # Return appropriately
    request.response.status_int = 200

    return doc_result


@service_single_daily.get(permission='authenticated')
def service_single_daily_get(request):
    _fitbitquery(request)

    # Parameters
    pid = request.matchdict['pid']
    date = request.matchdict['date']

    # Admin object
    admin = _get_admin(request)

    # Gather the documents it will need
    docs = {}
    docs['familysleep_personas'] = admin.get_document(doc_id='familysleep_personas')

    doc_id_fitbit_sleep = 'fitbit-{}-sleep-{}'.format(
        docs['familysleep_personas']['personas'][pid]['fitbit'],
        date
    )
    if admin.exists_document(doc_id=doc_id_fitbit_sleep):
        docs[doc_id_fitbit_sleep] = admin.get_document(doc_id_fitbit_sleep)

    # Compute the summary
    doc_result = _compute_single_daily(docs=docs, pid=pid, date=date, with_chart_data=True)

    # Return appropriately
    request.response.status_int = 200

    return doc_result


@service_single_weekly.get(permission='authenticated')
def service_single_weekly_get(request):
    _fitbitquery(request)

    # Parameters
    pid = request.matchdict['pid']
    date = request.matchdict['date']

    # Admin object
    admin = _get_admin(request)

    # Gather the documents it will need
    docs = {}
    docs['familysleep_personas'] = admin.get_document(doc_id='familysleep_personas')

    for days_back in reversed(range(0, 7)):
        current_date = datetime.datetime.strptime(date, '%Y-%m-%d') - datetime.timedelta(days=days_back)
        current_date = current_date.strftime('%Y-%m-%d')

        doc_id_fitbit_sleep = 'fitbit-{}-sleep-{}'.format(
            docs['familysleep_personas']['personas'][pid]['fitbit'],
            current_date
        )
        if admin.exists_document(doc_id=doc_id_fitbit_sleep):
            docs[doc_id_fitbit_sleep] = admin.get_document(doc_id_fitbit_sleep)

    # Compute the summary
    doc_result = _compute_single_weekly(docs=docs, pid=pid, date=date, with_chart_data=True)

    # Return appropriately
    request.response.status_int = 200

    return doc_result


def _fitbitquery(request):
    logs = []

    logs.append('initiating query')

    # Admin object
    admin = _get_admin(request)

    # Check we have what we'll need
    if not admin.exists_document(doc_id='familysleep_personas'):
        logs.append('no familysleep_personas document')
        return
    if not admin.exists_document(doc_id='fitbit_tokens'):
        logs.append('no familysleep_personas document')
        return

    # Get the personas
    doc_personas = admin.get_document(doc_id='familysleep_personas')

    # Get the fitbit tokens
    doc_fitbittokens = admin.get_document(doc_id='fitbit_tokens')
    fitbittokens_by_id = {
        token_current['user_id']: token_current for token_current in doc_fitbittokens['fitbit_tokens']
    }

    logs.append('got personas and tokens')

    # Start a session with Fitbit
    session_fitbit = requests.Session()

    # Go through the personas, check how long since we updated their data
    for key_current, persona_current in doc_personas['personas'].items():
        logs.append(
            'processing persona {}'.format(
                persona_current['name']
            )
        )

        # See when we updated and when we renewed
        datetime_now = datetime.datetime.now()
        timestamp_updated = persona_current.get('fitbit_updated', 0)
        timestamp_renewed = persona_current.get('fitbit_renewed', 0)
        timestamp_current = int(datetime_now.timestamp())
        timestamp_oldest_allowable_query = persona_current.get(
            'fitbit_oldest_allowable_query',
            (datetime_now - datetime.timedelta(days=7)).timestamp()
        )

        # Time since renewed
        logs.append(
            'time since renewed {}'.format(
                timestamp_current - timestamp_renewed
            )
        )

        if timestamp_current - timestamp_renewed > (4 * 60 * 60):
            logs.append('DO RENEW')

            # Get our renewal token
            refresh_token = fitbittokens_by_id[persona_current['fitbit']]['refresh_token']

            # Issue the renewal request
            response = session_fitbit.post(
                'https://api.fitbit.com/oauth2/token',
                headers={
                    'Authorization':
                        'Basic {}'.format(
                            base64.b64encode('{}:{}'.format(
                                request.registry.settings['secrets']['fitbit']['fitbit_id'],
                                request.registry.settings['secrets']['fitbit']['fitbit_secret']
                            ).encode('utf-8')).decode('utf-8')
                        )
                },
                data={
                    'grant_type': 'refresh_token',
                    'refresh_token': refresh_token,
                    'redirect_uri': request.registry.settings['secrets']['fitbit']['fitbit_redirect_uri']
                }
            )

            # Store our updated token
            fitbittokens_by_id[persona_current['fitbit']] = response.json()
            doc_fitbittokens['fitbit_tokens'] = list(fitbittokens_by_id.values())
            doc_fitbittokens.update(
                admin.update_document(
                    doc_fitbittokens
                )
            )

            # Store our updated renewal time
            persona_current['fitbit_renewed'] = timestamp_current
            doc_personas.update(
                admin.update_document(
                    doc_personas
                )
            )

        # Time since updated
        logs.append(
            'time since updated {}'.format(
                timestamp_current - timestamp_updated
            )
        )

        if timestamp_current - timestamp_updated > (10 * 60):
            logs.append('DO UPDATE')

            dates_query = [datetime_now - datetime.timedelta(days=x) for x in range(0, 60)]
            dates_query = [x for x in dates_query if x >= datetime.datetime.fromtimestamp(timestamp_oldest_allowable_query)]
            dates_query = [date.strftime('%Y-%m-%d') for date in dates_query]

            # Filter out documents where we already have more recent data, as they should be stable by now
            for index_current, date_current in enumerate(dates_query):
                doc_id = 'fitbit-{}-sleep-{}'.format(
                    persona_current['fitbit'],
                    date_current
                )

                if admin.exists_document(doc_id=doc_id):
                    # Document already exists, so we'll skip any documents 2 days older than this one
                    dates_query = dates_query[:min(len(dates_query), index_current + 2 + 1)]
                    break

            access_token = fitbittokens_by_id[persona_current['fitbit']]['access_token']

            # Query old dates in chronological order, so we don't have more recent data with gaps behind
            dates_query = reversed(dates_query)
            for date_current in dates_query:
                logs.append('query date {}'.format(date_current))

                doc_id = 'fitbit-{}-sleep-{}'.format(
                    persona_current['fitbit'],
                    date_current
                )

                response = session_fitbit.get(
                    'https://api.fitbit.com/1/user/{}/sleep/date/{}.json'.format(
                        persona_current['fitbit'],
                        date_current
                    ),
                    headers={
                        'Authorization':
                            'Bearer {}'.format(access_token)
                    }
                )

                data_fitbit = response.json()
                if 'sleep' in data_fitbit:
                    # Get the main sleep object
                    data_sleep = next(
                        (
                            entry for entry in data_fitbit['sleep'] if entry['isMainSleep']
                        ),
                        None
                    )

                    if data_sleep:  # not an empty list
                        logs.append('storing')

                        if admin.exists_document(doc_id=doc_id):
                            doc_rev = admin.get_document(doc_id=doc_id)['_rev']
                            admin.update_document(
                                doc=data_sleep,
                                doc_id=doc_id,
                                doc_rev=doc_rev
                            )
                        else:
                            admin.create_document(data_sleep, doc_id=doc_id)

            persona_current['fitbit_updated'] = timestamp_current
            if 'timestamp_oldest_allowable_query' not in persona_current:
                persona_current['timestamp_oldest_allowable_query'] = timestamp_oldest_allowable_query
            doc_personas.update(
                admin.update_document(
                    doc_personas
                )
            )

    # Return appropriately
    return {
        'logs': logs
    }


@service_fitbitquery.get(permission='authenticated')
def service_fitbitquery_get(request):
    request.response.status_int = 200

    return _fitbitquery(request)
