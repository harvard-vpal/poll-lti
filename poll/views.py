from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.base import TemplateView, View
from django.views.generic import DetailView
from .forms import QuestionForm
from .models import Question, Response, Choice
from .plots import results_pie
from ltiprovider.utils import update_lti_consumer_grade
from ltiprovider.mixins import LtiLaunchMixin, LtiSessionMixin

# Create your views here.
class IndexView(TemplateView):
    template_name = 'poll/hello.html'


class LaunchView(LtiLaunchMixin, View):
    def get(self, request, *args, **kwargs):
        question = get_object_or_404(Question, pk=request.GET.get('question'))
        response = Response.objects.filter(user=request.user, question=question).first()
        if response:
            return redirect('poll:results', pk=question.pk)
        else:
            return redirect('poll:question', pk=question.pk)


class QuestionView(LtiLaunchMixin, DetailView):
    template_name = 'poll/question.html'
    form_class = QuestionForm
    model = Question

    # TODO redirect to result page if learner has alrady answered the poll

    # def get(self):
    #     """
    #
    #     :return:
    #     """
    # question = get_object_or_404(Question, pk=request.GET.get('question'))
    # response = Response.objects.filter(user=request.user, question=question).first()
    # if response:
    #     return redirect('poll:results', pk=question.pk)
    # else:
    #     return redirect('poll:question', pk=question.pk)


    def get_context_data(self, **kwargs):
        """
        Inject the form object into the view context
        """
        context = super().get_context_data(**kwargs)
        context['form'] = self.form_class(self.object)  # self.object is the question model instance
        return context


class VoteView(LtiSessionMixin, DetailView):
    model = Question
    form_class = QuestionForm

    def post(self, request, *args, **kwargs):
        question = self.get_object()
        form = self.form_class(question, request.POST)
        if form.is_valid():
            # pass back grade to lti consumer
            score = 1.0  # score to pass back
            update_lti_consumer_grade(
                request.session['oauth_consumer_key'],
                request.session['oauth_consumer_secret'],
                request.session['lis_outcome_service_url'],
                request.session['lis_result_sourcedid'],
                score
            )

            # process form cleaned data
            Response.objects.create(user=request.user, question=question, choice=form.cleaned_data['choice'])
            return redirect('poll:results', question.id)


class ResultsView(LtiSessionMixin, DetailView):
    model = Question
    template_name = 'poll/results.html'

    def get_context_data(self, **kwargs):
        question = self.get_object()
        context = super().get_context_data(**kwargs)
        response = Response.objects.filter(user=self.request.user, question=question).first()
        context['response'] = response
        context['plot'] = results_pie(question)
        return context
