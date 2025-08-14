from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.db.models import Count
from datetime import timedelta
from django.utils import timezone
from app.models import Tag

class Command(BaseCommand):
    help = 'Update popular tags cache'

    def handle(self, *args, **options):
        three_months_ago = timezone.now() - timedelta(days=90)
        tags = Tag.objects.filter(questions__created_at__gte=three_months_ago).annotate(num_questions=Count('questions')
                                                                                        ).order_by('-num_questions')[:10]
        cache.set('popular_tags', list(tags.values('id', 'name', 'num_questions')), 3600 * 6)
