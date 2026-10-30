# Name: Stanley Lin
# BU Email: stanley0@bu.edu
# Description: Test CSV imports, combined filters, pagination, detail, and graph totals.
import csv
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import parse_qs, urlparse
from django.test import TestCase
from django.urls import reverse
from .models import Voter, ELECTIONS, load_data


class VoterViewsTests(TestCase):
    """Exercise listings, detail pages, and aggregate charts with fictional records."""

    @classmethod
    def setUpTestData(cls):
        """Create fictional voters for cls, the test class, once for all its tests."""
        cls.first = Voter.objects.create(voter_id='fiction-1', first_name='Alex', last_name='Example',
            street_number='12', street_name='Example & Test Road', apartment_number='2', zip_code='02458',
            date_of_birth=date(1975, 1, 1), date_of_registration=date(2000, 1, 1),
            party_affiliation='D', precinct_number='1', voter_score=4,
            v20state=True, v21town=True, v22general=True, v23town=True)
        cls.second = Voter.objects.create(voter_id='fiction-2', first_name='Sam', last_name='Sample',
            street_number='24', street_name='Fiction Lane', zip_code='02458',
            date_of_birth=date(2000, 12, 31), party_affiliation='U', precinct_number='2',
            voter_score=0)
        cls.third = Voter.objects.create(voter_id='fiction-3', first_name='Taylor', last_name='Demo',
            street_number='36', street_name='Fiction Lane', zip_code='02458',
            date_of_birth=date(2001, 1, 1), party_affiliation='D', precinct_number='3',
            voter_score=1, v21primary=True)

    def list_response(self, **parameters):
        """GET the voter list for self's client using parameters as URL filters."""
        return self.client.get(reverse('voter_analytics:voters'), parameters)

    def test_combined_and_inclusive_year_filters(self):
        """Verify self's list combines optional filters and includes both boundary years."""
        response = self.list_response(min_year=1975, max_year=2000)
        self.assertEqual(set(response.context['voters']), {self.first, self.second})
        response = self.list_response(min_year=1975, max_year=2000, voter_score=4, v20state='on', v21town='on')
        self.assertEqual(list(response.context['voters']), [self.first])
        self.assertContains(response, 'value="4" selected')
        self.assertContains(response, 'checked')
        response = self.list_response(party='D')
        self.assertEqual(set(response.context['voters']), {self.first, self.third})

    def test_each_election_and_zero_score(self):
        """Verify self's filters handle every election independently and the numeric score zero."""
        for field, _ in ELECTIONS:
            with self.subTest(field=field):
                response = self.list_response(**{field: 'on'})
                expected = self.third if field == 'v21primary' else self.first
                self.assertEqual(list(response.context['voters']), [expected])
        self.assertEqual(list(self.list_response(voter_score='0').context['voters']), [self.second])

    def test_invalid_and_empty_filters(self):
        """Verify self's invalid parameters show errors, while no parameters show all records."""
        self.assertEqual(self.list_response().context['paginator'].count, 3)
        for parameters in [{'min_year': 2000, 'max_year': 1975}, {'party': 'bogus'}, {'voter_score': 'six'}, {'min_year': 'bad'}]:
            with self.subTest(parameters=parameters):
                response = self.list_response(**parameters)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context['filter_form'].errors)
                self.assertEqual(response.context['paginator'].count, 0)
        response = self.list_response(party='U', v20state='on')
        self.assertContains(response, 'No voters match')

    def test_pagination_retains_filters(self):
        """Verify self's results show 100 records per page and preserve URL filters."""
        Voter.objects.bulk_create([Voter(voter_id=f'fiction-page-{i}', first_name='Page', last_name=f'Example{i:03}',
            street_number='1', street_name='Example Lane', zip_code='02458', date_of_birth=date(1980, 1, 1),
            party_affiliation='D', precinct_number='1', voter_score=0) for i in range(105)])
        response = self.list_response(party='D')
        self.assertEqual(len(response.context['voters']), 100)
        self.assertContains(response, '?party=D&amp;page=2')
        response = self.list_response(party='D', page=2)
        self.assertEqual(len(response.context['voters']), 7)

    def test_detail_and_map_encoding(self):
        """Verify self's voter detail includes fields, booleans, and a safely encoded map URL."""
        response = self.client.get(self.first.get_absolute_url())
        self.assertContains(response, 'Alex Example')
        self.assertContains(response, '1975-01-01')
        self.assertContains(response, '2000-01-01')
        self.assertContains(response, 'True')
        self.assertContains(response, 'False')
        self.assertEqual(parse_qs(urlparse(self.first.get_map_url()).query)['query'], [self.first.get_address()])
        self.assertEqual(self.client.get(reverse('voter_analytics:voter', args=[999999])).status_code, 404)

    def test_graph_counts_match_filtered_list(self):
        """Verify self's charts aggregate exactly the filtered records, including empty results."""
        response = self.client.get(reverse('voter_analytics:graphs'), {'party': 'D'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['result_count'], 2)
        self.assertEqual(sum(row['total'] for row in response.context['birth_counts']), 2)
        self.assertEqual(response.context['party_counts'], [{'party_affiliation': 'D', 'total': 2}])
        self.assertEqual(response.context['election_counts']['v20state'], 1)
        self.assertEqual(response.context['election_counts']['v21primary'], 1)
        self.assertContains(response, 'Plotly.newPlot', count=3)
        self.assertNotContains(response, '<script src=')
        response = self.client.get(reverse('voter_analytics:graphs'), {'party': 'U', 'v20state': 'on'})
        self.assertContains(response, 'No voters match')
        self.assertEqual(response.context['result_count'], 0)


class VoterImportTests(TestCase):
    """Exercise CSV parsing and repeatable imports without the full assignment dataset."""

    def write_csv(self, path, rows):
        """Write rows (CSV value lists) to path (a Path); self is the current test case."""
        header = ['Voter ID Number', 'Last Name', 'First Name', 'Residential Address - Street Number',
                  'Residential Address - Street Name', 'Residential Address - Apartment Number',
                  'Residential Address - Zip Code', 'Date of Birth', 'Date of Registration',
                  'Party Affiliation', 'Precinct Number'] + [field for field, _ in ELECTIONS] + ['voter_score']
        with path.open('w', encoding='utf-8-sig', newline='') as target:
            writer = csv.writer(target)
            writer.writerow(header)
            writer.writerows(rows)

    def test_import_dates_spaces_booleans_and_reimport(self):
        """Verify self's import preserves ZIPs, handles quoted commas/dates, and upserts IDs."""
        rows = [['fiction-id', 'Example, Jr.', 'Alex', '1', 'Demo Lane', '', '02458', '1980-02-29',
                 '06/04/2015', 'D ', '1', 'TRUE', 'FALSE', 'FALSE', 'FALSE', 'FALSE', '1'],
                ['fiction-invalid', 'Sample', 'Sam', '2', 'Demo Lane', '', '02458', '2000-01-01',
                 '1900-01-00', 'CC', '2', 'FALSE', 'FALSE', 'FALSE', 'FALSE', 'FALSE', '0']]
        with TemporaryDirectory(dir=Path(__file__).resolve().parent) as directory:
            path = Path(directory) / 'voters.csv'
            self.write_csv(path, rows)
            self.assertEqual(load_data(path), {'imported': 2, 'invalid_registration_dates': 1})
            voter = Voter.objects.get(voter_id='fiction-id')
            self.assertEqual(voter.last_name, 'Example, Jr.')
            self.assertEqual(voter.party_affiliation, 'D')
            self.assertEqual(voter.zip_code, '02458')
            self.assertTrue(voter.v20state)
            self.assertFalse(voter.v21town)
            self.assertEqual(voter.date_of_registration, date(2015, 6, 4))
            invalid = Voter.objects.get(voter_id='fiction-invalid')
            self.assertIsNone(invalid.date_of_registration)
            self.assertEqual(invalid.registration_date_original, '1900-01-00')
            self.assertContains(self.client.get(invalid.get_absolute_url()), '1900-01-00')
            rows[0][2] = 'Updated'
            self.write_csv(path, rows)
            load_data(path)
            self.assertEqual(Voter.objects.count(), 2)
            voter.refresh_from_db()
            self.assertEqual(voter.first_name, 'Updated')

    def test_invalid_csv_does_not_partially_import(self):
        """Verify self's malformed CSV raises an error without saving its earlier valid rows."""
        row = ['fiction-id', 'Example', 'Alex', '1', 'Demo Lane', '', '02458', '1980-01-01',
               '2000-01-01', 'U ', '1', 'FALSE', 'FALSE', 'FALSE', 'FALSE', 'FALSE', '0']
        with TemporaryDirectory(dir=Path(__file__).resolve().parent) as directory:
            path = Path(directory) / 'voters.csv'
            invalid = row.copy()
            invalid[0], invalid[11] = 'fiction-bad', 'NOT A BOOLEAN'
            self.write_csv(path, [row, invalid])
            with self.assertRaisesRegex(ValueError, 'CSV line 3'):
                load_data(path)
            self.assertEqual(Voter.objects.count(), 0)
            path.write_text('wrong,headers\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Missing CSV columns'):
                load_data(path)
