from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer
from rest_framework import serializers

from users.models import Subscription

User = get_user_model()


class CustomUserSerializer(UserSerializer):
    """Сериализатор пользователей."""

    class Meta:
        model = User
        fields = '__all__'


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор подписки."""

    #user = serializers.StringRelatedField(read_only=False)
    #course = serializers.StringRelatedField(read_only=False)

    class Meta:
        model = Subscription
        fields = (
            'user',
            'course'
        )
