from django.contrib.auth.models import AbstractUser
from django.db import models

#from courses.models import Course

class CustomUser(AbstractUser):
    """Кастомная модель пользователя - студента."""

    email = models.EmailField(
        verbose_name='Адрес электронной почты',
        max_length=250,
        unique=True
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = (
        'username',
        'first_name',
        'last_name',
        'password'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('-id',)

    def __str__(self):
        return self.get_full_name()


class Balance(models.Model):
    """Модель баланса пользователя."""

    user = models.OneToOneField(
        CustomUser, 
        on_delete = models.CASCADE,
        primary_key = True,
        verbose_name='Пользователь',
        related_name = 'balance'
    )
    bonus_count = models.PositiveIntegerField(
        verbose_name='Текущее количество бонусов',
        default = 1000,
        editable = False
    )

    class Meta:
        verbose_name = 'Баланс'
        verbose_name_plural = 'Балансы'
        ordering = ('-user',)


class Subscription(models.Model):
    """Модель подписки пользователя на курс."""
    user = models.ForeignKey(
        CustomUser,
        on_delete = models.CASCADE,
        verbose_name='Пользователь',
        related_name = 'subscriptions_on_courses'
    )
    course = models.ForeignKey(
        to='courses.Course',
        on_delete = models.CASCADE,
        verbose_name='Курс',
        related_name = 'subscriptions'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('-id',)

        constraints = [
            models.UniqueConstraint(
                fields = ['user', 'course'],
                name = 'Подписка пользователя на курс'
            )
        ]

