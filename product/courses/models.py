from django.db import models

class Course(models.Model):
    """Модель продукта - курса."""

    author = models.CharField(
        max_length=250,
        verbose_name='Автор',
    )
    title = models.CharField(
        max_length=250,
        verbose_name='Название',
    )
    start_date = models.DateTimeField(
        auto_now=False,
        auto_now_add=False,
        verbose_name='Дата и время начала курса'
    )
    price = models.PositiveIntegerField()

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'
        ordering = ('-id',)

    def __str__(self):
        return self.title


class Lesson(models.Model):
    """Модель урока."""

    title = models.CharField(
        max_length=250,
        verbose_name='Название',
    )
    link = models.URLField(
        max_length=250,
        verbose_name='Ссылка',
    )
    course = models.ForeignKey(
        Course,
        on_delete = models.CASCADE,
        verbose_name='Курс',
        related_name = 'lessons'
    )

    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'
        ordering = ('id',)

    def __str__(self):
        return self.title


class Group(models.Model):
    """Модель группы."""

    course = models.ForeignKey(
        Course,
        on_delete = models.CASCADE,
        verbose_name='Группа',
        related_name = 'groups'
    )
    users = models.ManyToManyField(
        to='users.CustomUser',
        verbose_name='Пользователи',
        related_name = 'groups_of_courses',
        blank = True
    )

    max_groups_per_course = 10
    max_subscribers_per_group = 30
    max_subscribers_per_course = max_groups_per_course * max_subscribers_per_group

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'
        ordering = ('-id',)
