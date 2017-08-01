import copy
import json
import nose.tools
import tests.data.test_familysleepdata
import tests.utilities
import tractdb_pyramid.views.familysleep_view


class TestFamilySleepView:
    @classmethod
    def setup_class(cls):
        cls.utilities = tests.utilities.Utilities('TestFamilySleepView')

        # Ensure we have a test account
        cls.utilities.ensure_fresh_account(
            cls.utilities.test_account_name(),
            cls.utilities.test_account_password()
        )

        # Create a client for the account
        cls.client = cls.utilities.client(
            account=cls.utilities.test_account_name(),
            password=cls.utilities.test_account_password()
        )

        # Create a session for the account
        cls.session = cls.utilities.session_pyramid(
            cls.utilities.test_account_name(),
            cls.utilities.test_account_password()
        )

        # Create our test documents
        for doc_id, doc in tests.data.test_familysleepdata.TestFamilySleepData().TEST_DATA:
            cls.client.create_document(
                doc=doc,
                doc_id=doc_id
            )

    @classmethod
    def teardown_class(cls):
        # Clean up our account
        cls.utilities.delete_account(
            cls.utilities.test_account_name()
        )

    def setup(self):
        cls = type(self)
        client = cls.client
        session = cls.session

    def teardown(self):
        cls = type(self)
        client = cls.client
        session = cls.session

    def test_compute_minutes_chart_data(self):
        fitbit_minute_data = tests.data.test_familysleepdata.TestFamilySleepData().TEST_DATA_DICT[
            'fitbit-{}-sleep-{}'.format('4KBZLY', '2017-06-07')
        ]['minuteData']

        minutes_chart_data = tractdb_pyramid.views.familysleep_view._compute_minutes_chart_data(
            fitbit_minute_data=fitbit_minute_data
        )

        # Each column in the chart should either:
        # - be all 0 because the person was not asleep
        # - have exactly one 3 in it
        for index in range(0, len(minutes_chart_data['one'])):
            values = [
                minutes_chart_data['one'][index],
                minutes_chart_data['two'][index],
                minutes_chart_data['three'][index],
            ]

            nose.tools.assert_in(
                sorted(values),
                [[0, 0, 0], [0, 0, 3]]
            )

        # The total number of 3 entries should be the same as the numbers Fitbit's minuteData within our times
        count_chart_data = 0
        for index in range(0, len(minutes_chart_data['one'])):
            values = [
                minutes_chart_data['one'][index],
                minutes_chart_data['two'][index],
                minutes_chart_data['three'][index],
            ]

            if sorted(values) == [0, 0, 3]:
                count_chart_data += 1

        count_fitbit_data = 0
        for current_fitbit_minute_entry in fitbit_minute_data:
            current_fitbit_minute = current_fitbit_minute_entry['dateTime']
            parsed_hour = int(current_fitbit_minute.split(':')[0])
            parsed_minute = int(current_fitbit_minute.split(':')[1])

            time_start = 17 * 60
            time_end = 8 * 60
            time_current = parsed_hour * 60 + parsed_minute

            if time_current < time_end or time_current > time_start:
                count_fitbit_data += 1

        nose.tools.assert_equal(count_chart_data, count_fitbit_data)

    def test_compute_family_daily(self):
        doc_computed = tractdb_pyramid.views.familysleep_view._compute_family_daily(
            docs=tests.data.test_familysleepdata.TestFamilySleepData().TEST_DATA_DICT,
            date='2017-06-07'
        )

        with open('tests/full/test_familysleepview_familydaily_dump.json', 'w', encoding='utf-8') as f:
            json.dump(doc_computed, f, sort_keys=True, indent=2)

        with open('tests/full/test_familysleepview_familydaily_reference.json', 'r', encoding='utf-8') as f:
            doc_reference = json.load(f)

        nose.tools.assert_equal(
            doc_computed,
            doc_reference
        )

    def test_compute_family_weekly(self):
        doc_computed = tractdb_pyramid.views.familysleep_view._compute_family_weekly(
            docs=tests.data.test_familysleepdata.TestFamilySleepData().TEST_DATA_DICT,
            date='2017-06-07'
        )

        with open('tests/full/test_familysleepview_familyweekly_dump.json', 'w', encoding='utf-8') as f:
            json.dump(doc_computed, f, sort_keys=True, indent=2)

        with open('tests/full/test_familysleepview_familyweekly_reference.json', 'r', encoding='utf-8') as f:
            doc_reference = json.load(f)

        nose.tools.assert_equal(
            doc_computed,
            doc_reference
        )

    def test_compute_single_daily(self):
        doc_computed = tractdb_pyramid.views.familysleep_view._compute_single_daily(
            docs=tests.data.test_familysleepdata.TestFamilySleepData().TEST_DATA_DICT,
            pid='m3',
            date='2017-06-07',
            with_chart_data=True
        )

        doc_computed_simplified = copy.deepcopy(doc_computed)
        for current_key in ['one', 'two', 'three', 'labels']:
            doc_computed_simplified['m3']['2017-06-07']['minuteData'][current_key] = \
                doc_computed_simplified['m3']['2017-06-07']['minuteData'][current_key][:5]
            doc_computed_simplified['m3']['2017-06-07']['minuteData'][current_key].append('.....')

        with open('tests/full/test_familysleepview_singledaily_dump.json', 'w', encoding='utf-8') as f:
            json.dump(doc_computed, f, sort_keys=True, indent=2)

        with open('tests/full/test_familysleepview_singledaily_dumpsimplified.json', 'w', encoding='utf-8') as f:
            json.dump(doc_computed_simplified, f, sort_keys=True, indent=2)

        with open('tests/full/test_familysleepview_singledaily_reference.json', 'r', encoding='utf-8') as f:
            doc_reference = json.load(f)

        with open('tests/full/test_familysleepview_singledaily_referencesimplified.json', 'r', encoding='utf-8') as f:
            doc_reference_simplified= json.load(f)

        nose.tools.assert_equal(
            doc_computed_simplified,
            doc_reference_simplified
        )

        nose.tools.assert_equal(
            doc_computed,
            doc_reference
        )

    def test_compute_single_daily_no_data(self):
        doc_computed = tractdb_pyramid.views.familysleep_view._compute_single_daily(
            docs=tests.data.test_familysleepdata.TestFamilySleepData().TEST_DATA_DICT,
            pid='m3',
            date='2010-01-01',
            with_chart_data=True
        )

        with open('tests/full/test_familysleepview_singledaily_nodata_dump.json', 'w', encoding='utf-8') as f:
            json.dump(doc_computed, f, sort_keys=True, indent=2)

        with open('tests/full/test_familysleepview_singledaily_nodata_reference.json', 'r', encoding='utf-8') as f:
            doc_reference = json.load(f)

        nose.tools.assert_equal(
            doc_computed,
            doc_reference
        )

    def test_compute_single_weekly(self):
        doc_computed = tractdb_pyramid.views.familysleep_view._compute_single_weekly(
            docs=tests.data.test_familysleepdata.TestFamilySleepData().TEST_DATA_DICT,
            pid='m3',
            date='2017-06-07',
            with_chart_data=True
        )

        doc_computed_simplified = copy.deepcopy(doc_computed)
        for current_date in ['2017-06-01', '2017-06-02', '2017-06-03', '2017-06-04', '2017-06-05', '2017-06-06', '2017-06-07']:
            for current_key in ['one', 'two', 'three', 'labels']:
                doc_computed_simplified['m3'][current_date]['minuteData'][current_key] = \
                    doc_computed_simplified['m3'][current_date]['minuteData'][current_key][:5]
                doc_computed_simplified['m3'][current_date]['minuteData'][current_key].append('.....')

        with open('tests/full/test_familysleepview_singleweekly_dump.json', 'w', encoding='utf-8') as f:
            json.dump(doc_computed, f, sort_keys=True, indent=2)

        with open('tests/full/test_familysleepview_singleweekly_dumpsimplified.json', 'w', encoding='utf-8') as f:
            json.dump(doc_computed_simplified, f, sort_keys=True, indent=2)

        with open('tests/full/test_familysleepview_singleweekly_reference.json', 'r', encoding='utf-8') as f:
            doc_reference = json.load(f)

        with open('tests/full/test_familysleepview_singleweekly_referencesimplified.json', 'r', encoding='utf-8') as f:
            doc_reference_simplified = json.load(f)

        nose.tools.assert_equal(
            doc_computed_simplified,
            doc_reference_simplified
        )

        nose.tools.assert_equal(
            doc_computed,
            doc_reference
        )

    def test_family_daily(self):
        cls = type(self)
        session = cls.session

        response = session.get(
            '{}/{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'familysleep/familydaily',
                '2017-06-07'
            )
        )
        nose.tools.assert_equal(response.status_code, 200)
        doc_response = response.json()

        with open('tests/full/test_familysleepview_familydaily_reference.json', 'r', encoding='utf-8') as f:
            doc_reference = json.load(f)

        nose.tools.assert_equal(
            doc_response,
            doc_reference
        )

    def test_family_weekly(self):
        cls = type(self)
        session = cls.session

        response = session.get(
            '{}/{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'familysleep/familyweekly',
                '2017-06-07'
            )
        )
        nose.tools.assert_equal(response.status_code, 200)
        doc_response = response.json()

        with open('tests/full/test_familysleepview_familyweekly_reference.json', 'r', encoding='utf-8') as f:
            doc_reference = json.load(f)

        nose.tools.assert_equal(
            doc_response,
            doc_reference
        )

    def test_single_daily(self):
        cls = type(self)
        session = cls.session

        response = session.get(
            '{}/{}/{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'familysleep/singledaily',
                'm3',
                '2017-06-07'
            )
        )
        nose.tools.assert_equal(response.status_code, 200)
        doc_response = response.json()

        with open('tests/full/test_familysleepview_singledaily_reference.json', 'r', encoding='utf-8') as f:
            doc_reference = json.load(f)

        nose.tools.assert_equal(
            doc_response,
            doc_reference
        )

    def test_single_weekly(self):
        cls = type(self)
        session = cls.session

        response = session.get(
            '{}/{}/{}/{}'.format(
                cls.utilities.url_base_pyramid(),
                'familysleep/singleweekly',
                'm3',
                '2017-06-07'
            )
        )
        nose.tools.assert_equal(response.status_code, 200)
        doc_response = response.json()

        with open('tests/full/test_familysleepview_singleweekly_response_dump.json', 'w', encoding='utf-8') as f:
            json.dump(doc_response, f, sort_keys=True, indent=2)

        with open('tests/full/test_familysleepview_singleweekly_reference.json', 'r', encoding='utf-8') as f:
            doc_reference = json.load(f)

        nose.tools.assert_equal(
            doc_response,
            doc_reference
        )
