import logging
from django.shortcuts import redirect, get_object_or_404
from django.views.generic.base import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView
from .forms import QuestionForm
from .models import Question, Response
from .plots import results_pie
from .lti import post_grade
from .mixins import LTIAuthMixin


logger = logging.getLogger(__name__)


# Test view
class IndexView(TemplateView):
    template_name = 'poll/hello.html'

    def dispatch(self, request, *args, **kwargs):
        logger.error("error - hello andrew")
        logger.info("info - hello andrew")
        return super().dispatch(request, *args, **kwargs)


@method_decorator(csrf_exempt, name='dispatch')
class LaunchView(LTIAuthMixin, LoginRequiredMixin, View):
    """
    LTI launch comes to this view, which redirects user to question or result view
    """
    # Specifies to LTIAuthMixin.dispatch() that this is the initial LTI launch
    request_type = 'initial'

    def post(self, request, *args, **kwargs):
        print(self.lti.user_roles(self.request))
        question = get_object_or_404(Question, pk=request.GET.get('question'))
        response = Response.objects.filter(user=request.user, question=question).first()
        if response:
            return redirect('poll:results', pk=question.pk)
        else:
            return redirect('poll:question', pk=question.pk)


class QuestionView(LTIAuthMixin, LoginRequiredMixin, DetailView):
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


class VoteView(LTIAuthMixin, LoginRequiredMixin, DetailView):
    model = Question
    form_class = QuestionForm

    def post(self, request, *args, **kwargs):
        question = self.get_object()
        form = self.form_class(question, request.POST)
        if form.is_valid():
            # only record responses for learners
            if 'learner' in self.lti.user_roles(self.request):
                # pass back grade to lti consumer
                post_grade(1.0, request, self.lti)
                # process form cleaned data: create response object
                Response.objects.create(user=request.user, question=question, choice=form.cleaned_data['choice'])
            return redirect('poll:results', question.id)


class ResultsView(LTIAuthMixin, LoginRequiredMixin, DetailView):
    model = Question
    template_name = 'poll/results.html'

    def get_context_data(self, **kwargs):
        question = self.get_object()
        context = super().get_context_data(**kwargs)
        response = Response.objects.filter(user=self.request.user, question=question).first()
        context['response'] = response
        context['plot'] = results_pie(question)
        return context
