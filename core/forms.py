# SpacedCode/core/forms.py

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Question, CompanyTag, PROBLEM_TYPE_CHOICES
from django_select2.forms import Select2TagWidget

class ReviewForm(forms.Form):
    rating = forms.IntegerField(
        min_value=1,
        max_value=5,
        widget=forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)]),
        label="Rate your recall of the question (1-5)"
    )
    explanation = forms.CharField(
        widget=forms.Textarea,
        required=False,
        label="Explain the solution to the question as if you are teaching someone else"
    )
    time_taken = forms.FloatField(
        min_value=0,
        widget=forms.NumberInput(attrs={'placeholder': 'Time taken (minutes)'}),
        label="Time taken to solve (in minutes)"
    )

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class QuestionForm(forms.ModelForm):
    company_tags = forms.ModelMultipleChoiceField(
        queryset=CompanyTag.objects.all(),
        required=False,
        widget=Select2TagWidget(
            attrs={
                'class': 'select2-tag',
                'data-placeholder': 'Type in a company and press enter',
                'style': 'width: 100%;',
            }
        )
    )

    class Meta:
        model = Question
        fields = ['text', 'link', 'problem_type', 'company_tags']
        widgets = {
            'problem_type': forms.Select(choices=PROBLEM_TYPE_CHOICES),
        }

    def clean_company_tags(self):
        tags = self.cleaned_data['company_tags']
        for tag in tags:
            CompanyTag.objects.get_or_create(name=tag.name)
        return tags