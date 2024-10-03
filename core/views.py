# SpacedCode/core/views.py
from django.db import models
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Question, ReviewSession
from .utils import FSRS, calculate_average_time
from .forms import ReviewForm, UserRegisterForm, QuestionForm
from datetime import datetime, timedelta, timezone


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Account created for {user.username}! You can now log in.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'core/register.html', {'form': form})

@login_required
def dashboard(request):
    user = request.user
    total_questions = Question.objects.filter(user=user).count()
    pending_reviews = Question.objects.filter(user=user, next_review__lte=datetime.today()).count()
    return render(request, 'core/dashboard.html', {
        'total_questions': total_questions,
        'pending_reviews': pending_reviews,
    })

@login_required
def add_question(request):
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.user = request.user
            question.save()
            form.save_m2m()
            messages.success(request, 'Question added successfully!')
            return redirect('dashboard')
    else:
        form = QuestionForm()
    return render(request, 'core/add_question.html', {'form': form})

@login_required
def edit_question(request, pk):
    question = get_object_or_404(Question, pk=pk, user=request.user)
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
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
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            rating = form.cleaned_data['rating']
            explanation = form.cleaned_data['explanation']
            time_taken = form.cleaned_data['time_taken']

            question.ratings.append({"date": datetime.now(timezone.utc).date().isoformat(), "rating": rating})
            question.current_retention_rate = sum(
                5 if r['rating'] >= 4 else r['rating'] for r in question.ratings
            ) / (len(question.ratings) * 5)

            difference_in_retention = abs(question.current_retention_rate - question.retention_factor) * 100
            if question.current_retention_rate > question.retention_factor:
                messages.success(request, f"You're hitting your retention goal! You're up by {difference_in_retention:.2f}%!")
            else:
                messages.warning(request, f"You're not hitting your retention goal. You're down by {difference_in_retention:.2f}%!")

            question.solving_time.append({"date": datetime.now(timezone.utc).date().isoformat(), "time_taken": time_taken})
            question.average_time = calculate_average_time(question.solving_time)

            update_question_metrics(fsrs, question, rating)

            question.feynman = explanation
            question.last_reviewed = datetime.now(timezone.utc).date().isoformat() #might have diff dates
            question.save()

            ReviewSession.objects.create(
                question=question,
                user=request.user,
                rating=rating,
                time_taken=time_taken,
                explanation=explanation
            )

            return redirect('review_list')
    else:
        form = ReviewForm()

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
    pending_reviews = Question.objects.filter(user=user, next_review__lte=datetime.today()).count()
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