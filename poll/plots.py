import plotly.offline as opy
import plotly.graph_objs as go
from django.db.models import Count
from poll.models import Choice


def results_pie(question, **kwargs):
    # get choices and sum responses for each
    choices = Choice.objects.filter(question=question).annotate(votes=Count('response'))
    choice_text, votes = list(zip(*choices.values_list('choice_text','votes')))

    # create plotly graph
    trace = go.Pie(labels=choice_text, values=votes)
    data = go.Data([trace])
    layout = go.Layout()
    figure = go.Figure(data=data,layout=layout)
    config = dict(
        displayModeBar=False,  # hide floating options toolbar
        showLink=False  # hide "export to plotly" link
    )
    div = opy.plot(figure, output_type='div', config=config)
    return div
