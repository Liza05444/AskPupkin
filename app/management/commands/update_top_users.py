from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.db.models import Sum, Q
from datetime import timedelta
from django.utils import timezone
from app.models import Profile

class Command(BaseCommand):
    help = 'Update top users cache'

    def handle(self, *args, **options):
        one_week_ago = timezone.now() - timedelta(days=7)
        users = Profile.objects.filter(Q(questions__created_at__gte=one_week_ago) | Q(answers__created_at__gte=one_week_ago)
                                       ).annotate(total_rating=Sum('questions__rating') + Sum('answers__rating')
                                                  ).order_by('-total_rating')[:10].select_related('user')
        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.user.username,
                'avatar': user.avatar.url if user.avatar else None,
                'rating': user.total_rating or 0
            })
        cache.set('top_users', users_data, 3600 * 6)
