# Name: Stanley Lin
# BU Email: stanley0@bu.edu
# Description: Model voter records and import the assignment CSV into the database.
import csv
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

from django.conf import settings
from django.core.validators import MaxValueValidator
from django.db import models, transaction
from django.urls import reverse


ELECTIONS = (
    ('v20state', '2020 State Election'),
    ('v21town', '2021 Town Election'),
    ('v21primary', '2021 Primary Election'),
    ('v22general', '2022 General Election'),
    ('v23town', '2023 Town Election'),
)


class Voter(models.Model):
    """Store one voter, address, dates, party, and election participation."""

    voter_id = models.CharField(max_length=30, unique=True)
    last_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    street_number = models.CharField(max_length=20)
    street_name = models.CharField(max_length=150)
    apartment_number = models.CharField(max_length=30, blank=True)
    zip_code = models.CharField(max_length=10)
    date_of_birth = models.DateField(db_index=True)
    date_of_registration = models.DateField(null=True, blank=True)
    registration_date_original = models.CharField(max_length=30, blank=True)
    party_affiliation = models.CharField(max_length=2, db_index=True)
    precinct_number = models.CharField(max_length=10)
    v20state = models.BooleanField(default=False)
    v21town = models.BooleanField(default=False)
    v21primary = models.BooleanField(default=False)
    v22general = models.BooleanField(default=False)
    v23town = models.BooleanField(default=False)
    voter_score = models.PositiveSmallIntegerField(validators=[MaxValueValidator(5)], db_index=True)

    class Meta:
        """Keep pagination deterministic when names repeat."""

        ordering = ['last_name', 'first_name', 'pk']

    def __str__(self):
        """Describe self, the current voter instance, by name and address."""
        return f'{self.first_name} {self.last_name}: {self.street_number} {self.street_name}'

    def get_absolute_url(self):
        """Return the detail URL for self, the current voter instance."""
        return reverse('voter_analytics:voter', kwargs={'pk': self.pk})

    def get_address(self):
        """Return the complete address for self, the current voter instance."""
        street = f'{self.street_number} {self.street_name}'
        if self.apartment_number:
            street += f', Apt {self.apartment_number}'
        return f'{street}, Newton, MA {self.zip_code}'

    def get_map_url(self):
        """Return an encoded Google Maps search for self's address."""
        return 'https://www.google.com/maps/search/?' + urlencode({'api': 1, 'query': self.get_address()})

    def get_election_history(self):
        """Return label/participation pairs for self, the current voter instance."""
        return [(label, getattr(self, field)) for field, label in ELECTIONS]


def parse_date(value):
    """Convert value, a CSV date string, to a date or raise ValueError."""
    for date_format in ('%Y-%m-%d', '%m/%d/%Y'):
        try:
            return datetime.strptime(value.strip(), date_format).date()
        except ValueError:
            continue
    raise ValueError(f'Invalid date: {value!r}')


def parse_boolean(value):
    """Convert value, a CSV TRUE/FALSE string, into a Python boolean."""
    normalized = value.strip().upper()
    if normalized not in ('TRUE', 'FALSE'):
        raise ValueError(f'Invalid election value: {value!r}')
    return normalized == 'TRUE'


def load_data(filename=None):
    """Import filename (a CSV path; defaults to BASE_DIR/newton_voters.csv).

    Upsert by source voter ID so repeated imports do not duplicate records.
    Preserve invalid registration dates verbatim instead of inventing dates.
    Return imported and invalid-registration-date counts. All writes are atomic.
    """
    filename = Path(filename) if filename is not None else settings.BASE_DIR / 'newton_voters.csv'
    text_columns = {
        'voter_id': 'Voter ID Number', 'last_name': 'Last Name',
        'first_name': 'First Name', 'street_number': 'Residential Address - Street Number',
        'street_name': 'Residential Address - Street Name',
        'apartment_number': 'Residential Address - Apartment Number',
        'zip_code': 'Residential Address - Zip Code', 'party_affiliation': 'Party Affiliation',
        'precinct_number': 'Precinct Number',
    }
    required = set(text_columns.values()) | {'Date of Birth', 'Date of Registration', 'voter_score'} | {field for field, _ in ELECTIONS}
    voters = []
    seen_ids = set()
    invalid_dates = 0
    with filename.open(encoding='utf-8-sig', newline='') as source:
        reader = csv.DictReader(source)
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f'Missing CSV columns: {sorted(missing)}')
        for line, row in enumerate(reader, start=2):
            try:
                values = {field: row[column].strip() for field, column in text_columns.items()}
                if not values['voter_id'] or values['voter_id'] in seen_ids:
                    raise ValueError('Missing or duplicate voter ID')
                seen_ids.add(values['voter_id'])
                values['date_of_birth'] = parse_date(row['Date of Birth'])
                original = row['Date of Registration'].strip()
                values['registration_date_original'] = ''
                try:
                    values['date_of_registration'] = parse_date(original)
                except ValueError:
                    values['date_of_registration'] = None
                    values['registration_date_original'] = original
                    invalid_dates += 1
                values.update({field: parse_boolean(row[field]) for field, _ in ELECTIONS})
                values['voter_score'] = int(row['voter_score'])
                if not 0 <= values['voter_score'] <= 5:
                    raise ValueError('Voter score must be between 0 and 5')
                if len(values['party_affiliation']) > 2:
                    raise ValueError('Party affiliation must be at most two characters')
                voters.append(Voter(**values))
            except (ValueError, AttributeError, TypeError) as error:
                raise ValueError(f'CSV line {line}: {error}') from error
    fields = [field.name for field in Voter._meta.fields if field.name not in ('id', 'voter_id')]
    with transaction.atomic():
        Voter.objects.bulk_create(voters, batch_size=500, update_conflicts=True,
                                  update_fields=fields, unique_fields=['voter_id'])
    return {'imported': len(voters), 'invalid_registration_dates': invalid_dates}
