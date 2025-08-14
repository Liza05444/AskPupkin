from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum
from datetime import timedelta
from django.utils import timezone


class TagManager(models.Manager):
    def popular_tags(self):
        return self.annotate(question_count=models.Count('questions')).order_by('-question_count')[:10]

    def get_tag_by_name(self, tag_name):
        return self.filter(name=tag_name).first()


class QuestionManager(models.Manager):
    def new_questions(self):
        return self.order_by('-created_at')

    def hot_questions(self):
        return self.order_by('-rating', '-created_at')

    def by_tag(self, tag_name):
        return self.filter(tags__name=tag_name).order_by('-created_at')


class AnswerManager(models.Manager):
    def for_question(self, question_id):
        return self.filter(question_id=question_id).order_by('created_at')


class ProfileManager(models.Manager):
    def best_users(self, days=7):
        date_from = timezone.now() - timedelta(days=days)
        return self.annotate(total_rating=Sum('questions__rating') + Sum('answers__rating')).filter(
            models.Q(questions__created_at__gte=date_from) | models.Q(answers__created_at__gte=date_from)
            ).order_by('-total_rating')[:5]


class Question(models.Model):
    author = models.ForeignKey('Profile', on_delete=models.CASCADE, related_name='questions')
    title = models.CharField(max_length=255)
    text = models.TextField()
    tags = models.ManyToManyField('Tag', related_name='questions')
    rating = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = QuestionManager()

    def update_rating(self):
        self.rating = QuestionLike.objects.filter(question=self).aggregate(models.Sum('value'))['value__sum'] or 0
        self.save()

    def get_user_vote(self, user_profile):
        if not user_profile:
            return 0
        vote = self.likes.filter(user=user_profile).first()
        return vote.value if vote else 0

    def toggle_vote(self, profile, value):
        current_vote = QuestionLike.objects.filter(question=self, user=profile).first()
        if current_vote and current_vote.value == value:
            current_vote.delete()
            user_vote = 0
        else:
            QuestionLike.objects.update_or_create(question=self, user=profile, defaults={'value': value})
            user_vote = value
        self.update_rating()
        self.refresh_from_db()
        return {'rating': self.rating, 'user_vote': user_vote}

    @classmethod
    def get_questions_with_votes(cls, questions, user_profile=None):
        if user_profile:
            questions_with_votes = []
            for question in questions:
                vote = QuestionLike.objects.filter(question=question, user=user_profile).first()
                user_vote = vote.value if vote else 0
                questions_with_votes.append((question, user_vote))
        else:
            questions_with_votes = [(question, 0) for question in questions]
        return questions_with_votes

    def __str__(self):
        return self.title


class Answer(models.Model):
    author = models.ForeignKey('Profile', on_delete=models.CASCADE, related_name='answers')
    text = models.TextField()
    is_correct = models.BooleanField(default=False)
    question = models.ForeignKey('Question', on_delete=models.CASCADE, related_name='answers')
    rating = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = AnswerManager()

    def update_rating(self):
        self.rating = AnswerLike.objects.filter(answer=self).aggregate(models.Sum('value'))['value__sum'] or 0
        self.save()

    def toggle_vote(self, profile, value):
        current_vote = AnswerLike.objects.filter(answer=self, user=profile).first()
        if current_vote and current_vote.value == value:
            current_vote.delete()
            user_vote = 0
        else:
            AnswerLike.objects.update_or_create(answer=self, user=profile, defaults={'value': value})
            user_vote = value
        self.update_rating()
        self.refresh_from_db()
        return {'rating': self.rating, 'user_vote': user_vote}

    def toggle_correct(self, user_profile):
        if self.question.author != user_profile:
            return {'error': "Only question's author can mark correct answer", 'success': False}
        self.is_correct = not self.is_correct
        self.save()
        return {'is_correct': self.is_correct, 'success': True}

    @classmethod
    def get_answers_with_votes(cls, answers, user_profile=None):
        answers_with_votes = []
        for answer in answers:
            answer_user_vote = 0
            if user_profile:
                vote = AnswerLike.objects.filter(answer=answer, user=user_profile).first()
                if vote:
                    answer_user_vote = vote.value
            answers_with_votes.append((answer, answer_user_vote))
        return answers_with_votes

    def __str__(self):
        return f"Answer to {self.question.title}"


class Tag(models.Model):
    name = models.CharField(max_length=30, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = TagManager()

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='images/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProfileManager()

    def __str__(self):
        return self.user.username


class QuestionLike(models.Model):
    CHOICES = [
        (1, 'Like'),
        (-1, 'Dislike')
    ]

    question = models.ForeignKey('Question', on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey('Profile', on_delete=models.CASCADE, related_name='question_likes')
    value = models.IntegerField(choices=CHOICES)

    class Meta:
        unique_together = [['user', 'question']]

    def __str__(self):
        if self.value == 1:
            return f"{self.user}: Like for {self.question}"
        return f"{self.user}: Dislike for {self.question}"


class AnswerLike(models.Model):
    CHOICES = [
        (1, 'Like'),
        (-1, 'Dislike')
    ]

    answer = models.ForeignKey('Answer', on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey('Profile', on_delete=models.CASCADE, related_name='answer_likes')
    value = models.IntegerField(choices=CHOICES)

    class Meta:
        unique_together = [['user', 'answer']]

    def __str__(self):
        if self.value == 1:
            return f"{self.user}: Like for {self.answer}"
        return f"{self.user}: Dislike for {self.answer}"
