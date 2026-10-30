# Name: Stanley Lin
# BU Email: stanley0@bu.edu
# Description: Validate optional voter filters shared by listings and graphs.
from django import forms
from django.db.models import Min, Max
from .models import Voter, ELECTIONS


class VoterFilterForm(forms.Form):
    """Collect optional party, inclusive birth years, score, and elections."""

    party = forms.ChoiceField(required=False, label='Party affiliation')
    min_year = forms.TypedChoiceField(required=False, coerce=int, empty_value=None, label='Minimum birth year')
    max_year = forms.TypedChoiceField(required=False, coerce=int, empty_value=None, label='Maximum birth year')
    voter_score = forms.TypedChoiceField(required=False, coerce=int, empty_value=None,
        choices=[('', 'Any score')] + [(score, score) for score in range(6)])
    v20state = forms.BooleanField(required=False, label='2020 State Election')
    v21town = forms.BooleanField(required=False, label='2021 Town Election')
    v21primary = forms.BooleanField(required=False, label='2021 Primary Election')
    v22general = forms.BooleanField(required=False, label='2022 General Election')
    v23town = forms.BooleanField(required=False, label='2023 Town Election')

    def __init__(self, *args, **kwargs):
        """Initialize self; args and kwargs are Django Form data/options."""
        super().__init__(*args, **kwargs)
        parties = Voter.objects.order_by('party_affiliation').values_list('party_affiliation', flat=True).distinct()
        self.fields['party'].choices = [('', 'All parties')] + [(party, party or '(Unspecified)') for party in parties if party]
        bounds = Voter.objects.aggregate(first=Min('date_of_birth'), last=Max('date_of_birth'))
        years = range(bounds['first'].year, bounds['last'].year + 1) if bounds['first'] else []
        choices = [('', 'Any year')] + [(year, year) for year in years]
        self.fields['min_year'].choices = choices
        self.fields['max_year'].choices = choices

    def clean(self):
        """Validate the year range on self, this bound filter form."""
        data = super().clean()
        minimum, maximum = data.get('min_year'), data.get('max_year')
        if minimum is not None and maximum is not None and minimum > maximum:
            raise forms.ValidationError('Minimum birth year cannot exceed maximum birth year.')
        return data


def filter_voters(queryset, form):
    """Filter queryset using form, a bound VoterFilterForm; invalid input returns none."""
    if not form.is_valid():
        return queryset.none()
    data = form.cleaned_data
    if data['party']:
        queryset = queryset.filter(party_affiliation=data['party'])
    if data['min_year'] is not None:
        queryset = queryset.filter(date_of_birth__year__gte=data['min_year'])
    if data['max_year'] is not None:
        queryset = queryset.filter(date_of_birth__year__lte=data['max_year'])
    if data['voter_score'] is not None:
        queryset = queryset.filter(voter_score=data['voter_score'])
    for field, _ in ELECTIONS:
        if data[field]:
            queryset = queryset.filter(**{field: True})
    return queryset
