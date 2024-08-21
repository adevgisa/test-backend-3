import pdb

from django.db.models import Count, Min
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from courses.models import Course, Group

from users.models import Subscription

@receiver(post_save, sender=Subscription)
def post_save_subscription(sender, instance: Subscription, created, **kwargs):
    """
    Распределение нового студента в группу курса.

    """

    if created:
        groups = Group.objects.filter(course=instance.course_id)\
            .select_related('course').prefetch_related('users').annotate(
                subscribers_count=Count('users'),
            ).order_by('subscribers_count')

        if not groups.exists():
            course = Course.objects.get(id=instance.course_id)
            group = Group.objects.create(course=course)
            group.users.add(instance.user_id)
        elif groups.count() < Group.max_groups_per_course:
            group = Group.objects.create(course=groups[0].course)
            group.users.add(instance.user_id)
        elif groups[0].subscribers_count < Group.max_subscribers_per_group:
            groups[0].users.add(instance.user_id)
        else:
            raise Group.TooManyStudentsInCourse()
