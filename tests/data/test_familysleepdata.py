import collections
import datetime
import json
import random
import uuid


class TestFamilySleepData:
    ID_Doc_Tuple = collections.namedtuple('ID_Doc_Tuple', ['doc_id', 'doc'])

    @property
    def TEST_DATA(self):
        data = []
        data.extend([
            TestFamilySleepData.ID_Doc_Tuple(
                'fitbit_tokens',
                self._TEST_TOKENS
            ),
            TestFamilySleepData.ID_Doc_Tuple(
                'familysleep_personas',
                self._TEST_PERSONAS
            )
        ])
        data.extend(self._TEST_SLEEP_DATA)

        return data

    @property
    def TEST_DATA_DICT(self):
        data = {}
        for doc_id, doc in self.TEST_DATA:
            if doc_id is None:
                doc_id = uuid.uuid4()

            data[doc_id] = doc

        return data

    @property
    def _TEST_SLEEP_DATA(self):
        # Configure the date range we will simulate
        simulate_start = datetime.datetime.strptime('2017-06-01', '%Y-%m-%d')
        simulate_end = datetime.datetime.strptime('2017-07-01', '%Y-%m-%d')
        dates_simulate = [simulate_start + datetime.timedelta(days=x) for x in
                          range(0, (simulate_end - simulate_start).days)]
        dates_simulate = [date.strftime('%Y-%m-%d') for date in dates_simulate]

        # Get the data we draw from to simulate
        with open('tests/data/test_familysleepdata.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            sample_historic_sleep_data = data['SAMPLE_HISTORIC_SLEEP_DATA']

        # Our list of simulated documents
        simulated_sleep_data = []

        # Simulate data for each of our people
        for persona_simulate in self._TEST_PERSONAS['personas'].values():
            # Use a consistent seed for testing
            persona_random = random.Random(persona_simulate['fitbit'])

            # Simulate data for each day in our range
            for date_simulate in dates_simulate:
                current_data_historic = persona_random.choice(sample_historic_sleep_data)
                current_data_simulate = dict(current_data_historic)

                current_data_simulate['startTime'] = current_data_simulate['startTime'].replace(
                    (datetime.datetime.strptime(current_data_historic['dateOfSleep'], '%Y-%m-%d') - datetime.timedelta(
                        days=1)).strftime('%Y-%m-%d'),
                    (datetime.datetime.strptime(date_simulate, '%Y-%m-%d') - datetime.timedelta(days=1)).strftime(
                        '%Y-%m-%d')
                )
                current_data_simulate['startTime'] = current_data_simulate['startTime'].replace(
                    current_data_historic['dateOfSleep'],
                    date_simulate
                )
                current_data_simulate['endTime'] = current_data_simulate['endTime'].replace(
                    current_data_historic['dateOfSleep'],
                    date_simulate
                )
                current_data_simulate['dateOfSleep'] = date_simulate

                doc_id = 'fitbit-{}-sleep-{}'.format(
                    persona_simulate['fitbit'],
                    current_data_simulate['dateOfSleep']
                )

                simulated_sleep_data.append(
                    TestFamilySleepData.ID_Doc_Tuple(
                        doc_id,
                        current_data_simulate
                    )
                )

        return simulated_sleep_data

    @property
    def _TEST_PERSONAS(self):
        return {
            'personas': {
                'm1': {
                    'name': 'Rob',
                    'targetedHours': 9,
                    'profilePic': 'images/avatars/momcircle.png',
                    'relation': 'parent',
                    'pid': 'm1',
                    'fitbit': '4KBZLY'
                },
                'm2': {
                    'name': 'Pat',
                    'targetedHours': 8,
                    'profilePic': 'images/avatars/dadcircle.png',
                    'relation': 'parent',
                    'pid': 'm2',
                    'fitbit': '4KB123'
                },
                'm3': {
                    'name': 'JR',
                    'targetedHours': 10,
                    'profilePic': 'images/avatars/girlcircle.png',
                    'relation': 'child',
                    'pid': 'm3',
                    'fitbit': '4KATL6'

                },
                'm4': {
                    'name': 'AJ',
                    'targetedHours': 10,
                    'profilePic': 'images/avatars/boycircle.png',
                    'relation': 'child',
                    'pid': 'm4',
                    'fitbit': '22TL6D'
                }
            }
        }

    @property
    def _TEST_TOKENS(self):
        return {
            'fitbit_tokens': {
                '_id': 'fitbit_tokens',
                '_rev': '1-e73c34cff5a766f172a405f916c44492',
                'fitbit_tokens': [
                    {
                        'access_token': 'DELETED',
                        'expires_in': 28800,
                        'refresh_token': 'DELETED',
                        'scope': 'activity heartrate weight sleep settings profile nutrition social location',
                        'token_type': 'Bearer',
                        'user_id': '4KBZLY'
                    },
                    {
                        'access_token': 'DELETED',
                        'expires_in': 28800,
                        'refresh_token': 'DELETED',
                        'scope': 'activity heartrate weight sleep settings profile nutrition social location',
                        'token_type': 'Bearer',
                        'user_id': '4KB123'
                    },
                    {
                        'access_token': 'DELETED',
                        'expires_in': 28800,
                        'refresh_token': 'DELETED',
                        'scope': 'activity heartrate weight sleep settings profile nutrition social location',
                        'token_type': 'Bearer',
                        'user_id': '4KATL6'
                    },
                    {
                        'access_token': 'DELETED',
                        'expires_in': 28800,
                        'refresh_token': 'DELETED',
                        'scope': 'weight activity settings location profile social heartrate nutrition sleep',
                        'token_type': 'Bearer',
                        'user_id': '22TL6D'
                    }
                ]
            }
        }

    def test_create_data(self):
        cls = type(self)

        data = self.TEST_DATA_DICT
