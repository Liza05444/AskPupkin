from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from faker import Faker
import random
from app.models import Profile, Tag, Question, Answer, QuestionLike, AnswerLike


class Command(BaseCommand):
    help = 'Fill database with fake data'

    def add_arguments(self, parser):
        parser.add_argument('ratio', type=int)

    def handle(self, *args, **kwargs):
        ratio = kwargs['ratio']
        fake = Faker()

        users = [User(username=f"{fake.user_name()}_{i}", email=fake.email()) for i in range(ratio)]
        User.objects.bulk_create(users, batch_size=1000)
        avatar_choices = ['images/avatar.png', 'images/avatar2.png', 'images/avatar3.png']
        profiles = [
            Profile(
                user=user,
                avatar=random.choice(avatar_choices)
            ) for user in users
        ]
        Profile.objects.bulk_create(profiles, batch_size=1000)

        tags = [Tag(name=f"{fake.word()}_{i}") for i in range(ratio)]
        Tag.objects.bulk_create(tags, batch_size=1000)

        questions = [
            Question(
                title=fake.sentence(),
                text=fake.text(),
                author=random.choice(profiles),
                rating=0
            ) for _ in range(ratio * 10)
        ]
        Question.objects.bulk_create(questions, batch_size=1000)

        for question in questions:
            question.tags.set(random.sample(tags, k=random.choice([1, 2, 3])))

        answers = [
            Answer(
                text=fake.text(),
                author=random.choice(profiles),
                question=random.choice(questions),
                rating=0,
                is_correct=random.choice([True, False])
            ) for _ in range(ratio * 100)
        ]
        Answer.objects.bulk_create(answers, batch_size=1000)

        question_likes = []
        answer_likes = []
        seen_question_likes = set()
        seen_answer_likes = set()
        for _ in range(ratio * 200):
            profile = random.choice(profiles)
            if random.choice([True, False]):
                question = random.choice(questions)
                key = (profile.id, question.id)
                if key not in seen_question_likes:
                    seen_question_likes.add(key)
                    question_likes.append(QuestionLike(
                        user=profile,
                        question=question,
                        value=random.choice([-1, 1])
                    ))
            else:
                answer = random.choice(answers)
                key = (profile.id, answer.id)
                if key not in seen_answer_likes:
                    seen_answer_likes.add(key)
                    answer_likes.append(AnswerLike(
                        user=profile,
                        answer=answer,
                        value=random.choice([-1, 1])
                    ))

        QuestionLike.objects.bulk_create(question_likes, batch_size=1000)
        AnswerLike.objects.bulk_create(answer_likes, batch_size=1000)

        question_ratings = {}
        for like in question_likes:
            question_ratings[like.question_id] = question_ratings.get(like.question_id, 0) + like.value
        for q in questions:
            q.rating = question_ratings.get(q.id, 0)
        Question.objects.bulk_update(questions, ['rating'], batch_size=1000)

        answer_ratings = {}
        for like in answer_likes:
            answer_ratings[like.answer_id] = answer_ratings.get(like.answer_id, 0) + like.value
        for a in answers:
            a.rating = answer_ratings.get(a.id, 0)
        Answer.objects.bulk_update(answers, ['rating'], batch_size=1000)

        self.stdout.write(self.style.SUCCESS(f'Successfully filled database with ratio {ratio}'))
