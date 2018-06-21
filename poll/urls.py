from django.urls import path, include

from . import views

app_name = 'poll'

urlpatterns = [
    path('hello/', views.IndexView.as_view(), name='hello'),
    path('<int:pk>/', views.QuestionView.as_view(), name='question'),
    path('<int:pk>/vote/', views.VoteView.as_view(), name='vote'),
    path('<int:pk>/results/', views.ResultsView.as_view(), name='results'),

    path('<int:pk>/test/', views.QuestionTestView.as_view(), name='question-test'),
]
