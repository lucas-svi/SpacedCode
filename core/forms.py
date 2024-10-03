# SpacedCode/core/forms.py

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Question

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
    class Meta:
        model = Question
        fields = ['text', 'link', 'problem_type', 'company_tags']
        widgets = {
            'company_tags': forms.CheckboxSelectMultiple(),
        }