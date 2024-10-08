# SpacedCode/core/views.py
from django.db import models
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import LogoutView, LoginView
from .models import Question, ReviewSession
from .utils import FSRS, calculate_average_time
from .forms import ReviewForm, UserRegisterForm, QuestionForm
from django.utils import timezone
from django.urls import reverse_lazy
from datetime import datetime, timedelta
import json
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Account created for {user.username}! You can now log in.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'registration/register.html', {'form': form})

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('dashboard')

    def form_valid(self, form):
        messages.success(self.request, f'Welcome back, {form.get_user().username}!')
        return super().form_valid(form)


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('dashboard')

    def dispatch(self, request, *args, **kwargs):
        messages.info(request, "You have been logged out successfully.")
        return super().dispatch(request, *args, **kwargs)


@login_required
def dashboard(request):
    user = request.user
    today = datetime.today().date()
    total_questions = Question.objects.filter(user=user).count()
    pending_reviews = Question.objects.filter(user=user, next_review__lte=today)
    pending_count = pending_reviews.count()
    all_questions = Question.objects.filter(user=user)

    return render(request, 'core/dashboard.html', {
        'total_questions': total_questions,
        'pending_reviews': pending_reviews, 
        'pending_count': pending_count,  
        'all_questions': all_questions,
    })



@login_required
def add_question(request):
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.user = request.user
            question.difficulty = 5 
            fsrs = FSRS()
            initial_stability = fsrs.w[0]
            question.stability = initial_stability
            question.interval = 1
            next_review_date = timezone.now() + timedelta(days=question.interval)
            question.next_review = next_review_date.date()
            question.save()
            form.save_m2m()
            messages.success(request, 'Question added successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = QuestionForm()
    return render(request, 'core/add_question.html', {'form': form})


@login_required
def edit_question(request, pk):
    question = get_object_or_404(Question, pk=pk, user=request.user)
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            question = form.save(commit=False)
            question.difficulty = question.difficulty
            question.next_review = question.next_review
            question.save()
            form.save_m2m()
            messages.success(request, 'Question updated successfully!')
            return redirect('dashboard')
    else:
        form = QuestionForm(instance=question)
    return render(request, 'core/edit_question.html', {'form': form, 'question': question})


@login_required
def delete_question(request, pk):
    question = get_object_or_404(Question, pk=pk, user=request.user)
    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Question deleted successfully!')
        return redirect('dashboard')
    return render(request, 'core/delete_question.html', {'question': question})

@login_required
def review_list(request):
    user = request.user
    questions = Question.objects.filter(user=user, next_review__lte=datetime.today())
    return render(request, 'core/review_list.html', {'questions': questions})

@login_required
def review_question(request, pk):
    question = get_object_or_404(Question, pk=pk, user=request.user)
    fsrs = FSRS()
    session_key = f'start_time_{question.id}'
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            rating = form.cleaned_data['rating']
            explanation = form.cleaned_data['explanation']
            start_time_str = request.session.get(session_key)
            if start_time_str:
                start_time = timezone.now()
                end_time = timezone.now()
                time_taken = (end_time - start_time).total_seconds() / 60
                del request.session[session_key]
            else:
                time_taken = 0

            if not question.ratings:
                question.ratings = []
            if not question.solving_time:
                question.solving_time = []

            question.ratings.append({
                "date": timezone.now().date().isoformat(),
                "rating": rating
            })
            question.solving_time.append({
                "date": timezone.now().date().isoformat(),
                "time_taken": time_taken
            })  
            
            last_stability = question.stability
            last_difficulty = question.difficulty
            retrievability = fsrs.forgetting_curve(question.interval, last_stability)
            new_stability = fsrs.next_recall_stability(
                last_difficulty, last_stability, retrievability, rating
            )
            new_difficulty = fsrs.next_difficulty(last_difficulty, rating)
            retention_factor = question.retention_factor
            base_interval = fsrs.next_interval(new_stability, retention_factor)

            if rating == 1:
                base_interval = 1
                new_stability = max(new_stability * 0.6, 0.1)

            new_interval = min(base_interval, fsrs.maximum_interval)
            next_review = timezone.now() + timedelta(days=new_interval)
            question.interval = new_interval
            question.stability = new_stability
            question.difficulty = new_difficulty
            question.next_review = next_review.date()
            question.last_reviewed = timezone.now().date()
            question.feynman = explanation
            average_time = calculate_average_time(question.solving_time, time_taken)
            question.average_time = average_time 

            question.save()

            messages.success(request, 'Review completed successfully!')
            return redirect('dashboard')
    else:
        form = ReviewForm()
        request.session[session_key] = timezone.now().isoformat()

    return render(request, 'core/review_question.html', {'question': question, 'form': form})

def update_question_metrics(fsrs, question, rating):
    last_interval = question.interval
    last_stability = question.stability
    last_difficulty = question.difficulty
    retention_factor = question.retention_factor

    retrievability = fsrs.forgetting_curve(last_interval, last_stability)
    new_stability = fsrs.next_recall_stability(last_difficulty, last_stability, retrievability, rating)
    new_difficulty = fsrs.next_difficulty(last_difficulty, rating)
    base_interval = fsrs.next_interval(new_stability, retention_factor)

    if rating == 1:
        base_interval = 1
        new_stability = max(new_stability * 0.6, 0.1)

    new_interval = min(base_interval, fsrs.maximum_interval)
    next_review = (datetime.now(timezone.utc) + timedelta(days=new_interval)).date().isoformat()

    question.interval = new_interval
    question.stability = new_stability
    question.difficulty = new_difficulty
    question.next_review = next_review




@login_required
def statistics(request):
    user = request.user
    total_questions = Question.objects.filter(user=user).count()
    reviewed_questions = Question.objects.filter(user=user, last_reviewed__isnull=False).count()
    pending_reviews = Question.objects.filter(user=user, next_review__lte=datetime.today().date()).count()
    average_difficulty = Question.objects.filter(user=user).aggregate(models.Avg('difficulty'))['difficulty__avg'] or 0
    average_solving_time = Question.objects.filter(user=user).aggregate(models.Avg('average_time'))['average_time__avg'] or 0

    context = {
        'total_questions': total_questions,
        'reviewed_questions': reviewed_questions,
        'pending_reviews': pending_reviews,
        'average_difficulty': round(average_difficulty, 2),
        'average_solving_time': round(average_solving_time, 2),
    }
    return render(request, 'core/statistics.html', context)