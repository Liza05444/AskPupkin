from app.models import Answer, Question
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage


def paginate_objects(objects_list, request, per_page=5):
    paginator = Paginator(objects_list, per_page)
    page_number = request.GET.get('page')
    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)
    return page


def prepare_questions_with_votes(questions, request):
    user_profile = request.user.profile if request.user.is_authenticated else None
    questions_with_votes = Question.get_questions_with_votes(questions, user_profile)
    page = paginate_objects([q[0] for q in questions_with_votes], request)
    questions_votes_map = {q[0].id: q[1] for q in questions_with_votes}
    current_page_with_votes = [(q, questions_votes_map.get(q.id, 0)) for q in page.object_list]
    return {'questions': page.object_list, 'questions_with_votes': current_page_with_votes, 'page': page}


def prepare_answers_with_votes(answers, request, user_profile):
    answers_with_votes = Answer.get_answers_with_votes(answers, user_profile)
    page = paginate_objects([a[0] for a in answers_with_votes], request)
    answers_votes_map = {a[0].id: a[1] for a in answers_with_votes}
    current_page_with_votes = [(a, answers_votes_map.get(a.id, 0)) for a in page.object_list]
    return {'answers': page.object_list, 'answers_with_votes': current_page_with_votes, 'page': page}
