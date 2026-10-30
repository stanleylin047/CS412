# Name: Stanley Lin
# BU Email: stanley0@bu.edu
# Description: Display filtered voter lists, detail records, and Plotly summaries.
import plotly.graph_objects as go
from django.db.models import Count, Q
from django.db.models.functions import ExtractYear
from django.views.generic import ListView, DetailView
from .forms import VoterFilterForm, filter_voters
from .models import Voter, ELECTIONS


class VoterFilterMixin:
    """Share form validation and filtering between the list and graph views."""

    def get_queryset(self):
        """Return voters filtered by self.request.GET, the current URL parameters."""
        self.filter_form = VoterFilterForm(self.request.GET)
        return filter_voters(Voter.objects.all(), self.filter_form)

    def get_context_data(self, **kwargs):
        """Add filters and URLs to self's template context; kwargs holds parent context."""
        context = super().get_context_data(**kwargs)
        parameters = self.request.GET.copy()
        parameters.pop('page', None)
        context['filter_query'] = parameters.urlencode()
        context['filter_form'] = self.filter_form
        return context


class VotersListView(VoterFilterMixin, ListView):
    """Show 100 matching voters per page, with stable ordering."""

    model = Voter
    template_name = 'voter_analytics/voters.html'
    context_object_name = 'voters'
    paginate_by = 100


class VoterDetailView(DetailView):
    """Show every stored field for the voter selected by URL primary key."""

    model = Voter
    template_name = 'voter_analytics/voter.html'
    context_object_name = 'voter'


class GraphsView(VoterFilterMixin, ListView):
    """Summarize all matching records, rather than only a page of records."""

    model = Voter
    template_name = 'voter_analytics/graphs.html'
    context_object_name = 'voters'

    def get_context_data(self, **kwargs):
        """Build three Plotly divs for self's filtered records; kwargs is parent context."""
        context = super().get_context_data(**kwargs)
        voters = self.object_list
        births = list(voters.order_by().annotate(year=ExtractYear('date_of_birth')).values('year').annotate(total=Count('pk')).order_by('year'))
        parties = list(voters.order_by().values('party_affiliation').annotate(total=Count('pk')).order_by('party_affiliation'))
        participation = voters.aggregate(**{field: Count('pk', filter=Q(**{field: True})) for field, _ in ELECTIONS})
        figures = [
            go.Figure(go.Bar(x=[row['year'] for row in births], y=[row['total'] for row in births])),
            go.Figure(go.Pie(labels=[row['party_affiliation'] or 'Unspecified' for row in parties], values=[row['total'] for row in parties])),
            go.Figure(go.Bar(x=[label for _, label in ELECTIONS], y=[participation[field] for field, _ in ELECTIONS])),
        ]
        titles = ['Voters by birth year', 'Voters by party affiliation', 'Participation in recent elections']
        divs = []
        for index, (figure, title) in enumerate(zip(figures, titles)):
            figure.update_layout(title=title, template='plotly_white', autosize=True, margin=dict(l=60, r=25, t=65, b=90))
            if index != 1:
                figure.update_yaxes(title_text='Number of voters', rangemode='tozero')
                figure.update_xaxes(title_text='Birth year' if index == 0 else 'Election')
            divs.append(figure.to_html(full_html=False, include_plotlyjs=index == 0, config={'responsive': True, 'displaylogo': False}))
        context.update(birth_graph=divs[0], party_graph=divs[1], election_graph=divs[2],
                       result_count=voters.count(), birth_counts=births, party_counts=parties,
                       election_counts=participation)
        return context
