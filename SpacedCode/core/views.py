# SpacedCode/core/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Question, ReviewSession
from .utils import FSRS, calculate_average_time
from .forms import ReviewForm
from datetime import datetime, timedelta, timezone

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