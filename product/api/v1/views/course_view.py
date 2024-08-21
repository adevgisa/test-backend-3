import pdb

from django.contrib.auth import get_user_model
from django.db.models import FilteredRelation, Q, Prefetch, F, Count, Max
from django.http import Http404
from django.shortcuts import get_object_or_404

from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from api.v1.permissions import IsStudentOrIsAdmin, ReadOnlyOrIsAdmin
from api.v1.serializers.course_serializer import (CourseSerializer,
                                                  CreateCourseSerializer,
                                                  CreateGroupSerializer,
                                                  CreateLessonSerializer,
                                                  GroupSerializer,
                                                  LessonSerializer)
from api.v1.serializers.user_serializer import SubscriptionSerializer

from courses.models import Course, Group

from users.models import Balance, Subscription

User = get_user_model()


class LessonViewSet(viewsets.ModelViewSet):
    """Уроки."""

    permission_classes = (IsStudentOrIsAdmin,)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return LessonSerializer
        return CreateLessonSerializer

    def perform_create(self, serializer):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        serializer.save(course=course)

    def get_queryset(self):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        return course.lessons.all()


class GroupViewSet(viewsets.ModelViewSet):
    """Группы."""

    permission_classes = (permissions.IsAdminUser,)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return GroupSerializer
        return CreateGroupSerializer

    def perform_create(self, serializer):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        serializer.save(course=course)

    def get_queryset(self):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        return course.groups.all()


class CourseViewSet(viewsets.ModelViewSet):
    """Курсы """

    queryset = Course.objects.all()
    permission_classes = (ReadOnlyOrIsAdmin,)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return CourseSerializer
        return CreateCourseSerializer

    def list(self, request):
        if request.user.is_authenticated and not request.user.is_staff:
            qs = Subscription.objects.filter(user=request.user.id).values('course')
            self.queryset = Course.objects.exclude(id__in=qs).prefetch_related('lessons')

        return super(CourseViewSet, self).list(request)

    @action(
        methods=['post'],
        detail=True,
        permission_classes=(permissions.IsAuthenticated,)
    )
    def pay(self, request, pk):
        """Покупка доступа к курсу (подписка на курс)."""

        queryset = Course.objects.filter(id=pk).annotate(
            subscriptions_user=FilteredRelation(
                'subscriptions', 
                condition=Q(subscriptions__user=request.user)
            ),
            course_groups=FilteredRelation(
                'groups',
                condition=Q(groups__course=pk)
            ),
            subscribers_count = Count("groups__users")
        ).values('id', 'price', 'subscriptions_user__user', 'subscribers_count')

        if not queryset.exists():
            raise Http404()

        course = queryset[0]

        if course['subscriptions_user__user'] is None:
            if course['subscribers_count'] >= Group.max_subscribers_per_course:
                return Response(
                    data = {
                        'error': 'Вы не можете подписаться на данный курс, т.к. все группы заполнены'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            balance = Balance.objects.get(user=request.user.id)
            if balance.bonus_count < course['price']:
                return Response(
                    data = {
                        'error': 'У вас недостаточно бонусов, чтобы подписаться на этот курс'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            data = {
                'user': request.user.id,
                'course': course['id'],
            }
            serializer = SubscriptionSerializer(data=data)
            if serializer.is_valid():
                balance.bonus_count -= course['price']
                balance.save(update_fields=['bonus_count'])
                serializer.save()
                return Response(
                    data=data,
                    status=status.HTTP_201_CREATED
                )

            return Response(
                data=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            data={'error': 'Вы уже подписаны на этот курс'},
            status=status.HTTP_400_BAD_REQUEST
        )
