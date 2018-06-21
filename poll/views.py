from django.shortcuts import redirect
from django.views.generic.base import TemplateView
from django.views.generic import DetailView

from ltiprovider.outcomes import update_grade
from ltiprovider.mixins import LtiLaunchMixin, LtiSessionMixin

from .forms import QuestionForm
from .models import Question, Response
from .plots import results_pie


class IndexView(TemplateView):
    template_name = 'poll/hello.html'


class QuestionView(LtiLaunchMixin, DetailView):
    template_name = 'poll/question.html'
    form_class = QuestionForm
    model = Question

    def post(self, request, *args, **kwargs):
        question = self.get_object()
        lti_user = self.get_lti_user()
        response = Response.objects.filter(lti_user=lti_user, question=question)
        # Redirect to result page if learner has alrady answered the poll
        if response.exists():
            return redirect('poll:results', pk=question.pk)

        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        Inject the form object into the view context
        """
        context = super().get_context_data(**kwargs)
        context['form'] = self.form_class(self.object)  # self.object is the question model instance
        return context


class QuestionTestView(DetailView):
    template_name = 'poll/question.html'
    form_class = QuestionForm
    model = Question

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
            update_grade(request.session, score)

            # process form cleaned data
            Response.objects.create(
                lti_user=self.get_lti_user(),
                question=question,
                choice=form.cleaned_data['choice']
            )
            return redirect('poll:results', question.id)


class ResultsView(LtiSessionMixin, DetailView):
    model = Question
    template_name = 'poll/results.html'

    def get_context_data(self, **kwargs):
        question = self.get_object()
        context = super().get_context_data(**kwargs)
        lti_user = self.get_lti_user()
        response = Response.objects.filter(lti_user=lti_user, question=question).first()
        context['response'] = response
        context['plot'] = results_pie(question)
        return context
