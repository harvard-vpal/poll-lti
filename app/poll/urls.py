from django.urls import path

from . import views

app_name = 'poll'

urlpatterns = [
    path('hello/', views.IndexView.as_view(), name='hello'),
    path('launch/', views.LaunchView.as_view(), name='launch'),
    path('<int:pk>/question/', views.QuestionView.as_view(), name='question'),
    path('<int:pk>/vote/', views.VoteView.as_view(), name='vote'),
    path('<int:pk>/results/', views.ResultsView.as_view(), name='results'),
]
