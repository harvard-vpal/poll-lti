from django import forms


class QuestionForm(forms.Form):
    """
    Input form for the poll question
    """
    choice = forms.ModelChoiceField(
        queryset=None,  # set queryset in init
        widget=forms.RadioSelect,   # radio select buttons instead of drop down select
        empty_label=None,   # disable display of empty label as choice
    )

    def __init__(self, question, *args, **kwargs):
        """
        'question' argument (Question model instance) added as form init parameter,
        in order to retrieve question text and answer choices
        """
        super().__init__(*args, **kwargs)
        # display related answer choices for this question
        self.fields['choice'].queryset = question.choice_set.all()
        self.fields['choice'].label = question.question_text
