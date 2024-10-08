# SpacedCode/core/forms.py

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Question, CompanyTag, PROBLEM_TYPE_CHOICES

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
    company_tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control select2-tag',
            'style': 'width: 100%;',
            'placeholder': 'Type in a company and press enter',
        })
    )
    link = forms.URLField(
        required=True
    )

    class Meta:
        model = Question
        fields = ['text', 'link', 'problem_type', 'company_tags']
        
        widgets = {
            'problem_type': forms.Select(choices=PROBLEM_TYPE_CHOICES),
        }
        

    def clean_company_tags(self):
        tags_str = self.cleaned_data.get('company_tags', '')
        tag_names = [name.strip() for name in tags_str.split(',') if name.strip()]
        tags = []
        for name in tag_names:
            tag, created = CompanyTag.objects.get_or_create(name=name)
            tags.append(tag)
        self.cleaned_data['company_tags'] = tags
        return tags

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            instance.company_tags.set(self.cleaned_data['company_tags'])
        return instance