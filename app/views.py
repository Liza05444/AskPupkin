from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.decorators.http import require_POST
from django.db.models import Q

from .models import Tag, Question, Answer
from .forms import LoginForm, SignUpForm, ProfileSettingsForm, AnswerForm, AskQuestionForm
from .service import prepare_answers_with_votes, prepare_questions_with_votes
from .centrifugo import publish_to_centrifugo, generate_token

from django.conf import settings


def index(request):
    questions = Question.objects.new_questions()
    context = prepare_questions_with_votes(questions, request)
    return render(request, 'index.html', context)


def hot(request):
    questions = Question.objects.hot_questions()
    context = prepare_questions_with_votes(questions, request)
    return render(request, 'hot.html', context)


def tag(request, tag_name):
    chosen_tag = get_object_or_404(Tag, name=tag_name)
    questions = Question.objects.by_tag(tag_name)
    context = prepare_questions_with_votes(questions, request)
    context['tag'] = chosen_tag
    return render(request, 'tag.html', context)


def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            next_url = request.GET.get('next', 'index')
            return redirect(next_url)
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


def logout(request):
    auth_logout(request)
    next_url = request.META.get('HTTP_REFERER')
    if next_url:
        return redirect(next_url)
    return redirect('index')


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST, request.FILES)
        if form.is_valid():
            form.save(request)
            return redirect('index')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})


@login_required(login_url=reverse_lazy('login'))
def settings_profile(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileSettingsForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save(request)
            messages.success(request, 'Profile updated successfully')
            return redirect('profile_edit')
    else:
        form = ProfileSettingsForm(instance=profile)
    return render(request, 'settings.html', {'form': form, 'profile': profile})


@login_required(login_url=reverse_lazy('login'))
def ask(request):
    if request.method == 'POST':
        form = AskQuestionForm(request.POST)
        if form.is_valid():
            my_question = form.save(author=request.user.profile)
            return redirect(reverse('question', kwargs={'question_id': my_question.id}))
    else:
        form = AskQuestionForm()
    return render(request, 'ask.html', {'form': form})


def question(request, question_id):
    single_question = get_object_or_404(Question, pk=question_id)
    answers = Answer.objects.for_question(question_id)
    user_profile = request.user.profile if request.user.is_authenticated else None
    question_user_vote = single_question.get_user_vote(user_profile)
    answers_context = prepare_answers_with_votes(answers, request, user_profile)

    form = AnswerForm()
    if request.method == 'POST':
        form = AnswerForm(request.POST)
        if form.is_valid():
            answer = form.save(author=request.user.profile, question=single_question)
            publish_to_centrifugo(channel=f"question_{question_id}", answer=answer)
            page_number = answers.count() // answers_context['page'].paginator.per_page + 1
            url = reverse('question', kwargs={'question_id': single_question.id})
            return redirect(f"{url}?page={page_number}#answer-{answer.id}")

    centrifugo_token = generate_token(request.user.pk if request.user.is_authenticated else None)
    return render(request, 'single_question.html', {
        'question': single_question, 'answers': answers_context['answers'], 'page': answers_context['page'], 'form': form,
        'answers_with_votes': answers_context['answers_with_votes'], 'user_vote': question_user_vote,
        'centrifugo_token': centrifugo_token, 'centrifugo_channel': f"question_{question_id}", "ws_url": settings.CENTRIFUGO_URL
    })


@require_POST
@login_required
def mark_correct_answer(request):
    answer_id = request.POST.get('answer_id')
    try:
        answer = get_object_or_404(Answer, pk=answer_id)
        result = answer.toggle_correct(request.user.profile)
        if not result['success']:
            return JsonResponse({'error': result['error']}, status=403)
        return JsonResponse({'is_correct': result['is_correct']})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_POST
@login_required
def question_like(request):
    try:
        question_id = request.POST.get('question_id')
        value = int(request.POST.get('value', 0))
        this_question = get_object_or_404(Question, pk=question_id)
        result = this_question.toggle_vote(request.user.profile, value)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_POST
@login_required
def answer_like(request):
    try:
        answer_id = request.POST.get('answer_id')
        value = int(request.POST.get('value', 0))
        answer = get_object_or_404(Answer, pk=answer_id)
        result = answer.toggle_vote(request.user.profile, value)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def search_suggestions(request):
    query = request.GET.get('q', '').strip()
    if len(query) < 3:
        return JsonResponse({'results': []})
    results = Question.objects.filter(Q(title__icontains=query) | Q(text__icontains=query))[:5]
    suggestions = [{
        'title': q.title,
        'content': q.text[:30] + '...' if len(q.text) > 30 else q.text,
        'url': f'/question/{q.id}/'
    } for q in results]
    return JsonResponse({'results': suggestions})
