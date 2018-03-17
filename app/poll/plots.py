import plotly.offline as opy
import plotly.graph_objs as go
from django.db.models import Count
from poll.models import Choice


def results_pie(question, **kwargs):
    # get choices and sum responses for each
    choices = Choice.objects.filter(question=question).annotate(votes=Count('response'))
    choice_text, votes = list(zip(*choices.values_list('choice_text','votes')))

    trace = go.Pie(labels=choice_text, values=votes)
    data = go.Data([trace])
    layout = go.Layout(title=question.question_text)
    figure = go.Figure(data=data,layout=layout)
    div = opy.plot(figure, auto_open=False, output_type='div', show_link=False)

    return div
