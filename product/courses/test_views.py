import pdb

from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIRequestFactory

from users.models import Balance, Subscription

from .models import Course, Group

User = get_user_model()

def create_courses():
    Course.objects.bulk_create([
        Course(author='Author',title='title',start_date=timezone.now(),
            price=100),
        Course(author='Author2',title='title2',start_date=timezone.now(),
            price=200),
        Course(author='Author3',title='title3',start_date=timezone.now(),
            price=300),
        Course(author='Author4',title='title4',start_date=timezone.now(),
            price=400),
    ])

class CourseTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username='admin',
            first_name='test',
            last_name='test',
            email='admin@example.com',
            password='Test1234'
        )
        self.superuser.token = str(
            Token.objects.get_or_create(user=self.superuser)[0]
        )

        self.user = User.objects.create_user(
            username='user',
            first_name='testuser',
            last_name='testuser',
            email='user@example.com',
            password='Test1234',
        )
        self.user.token = str(
            Token.objects.get_or_create(user=self.user)[0]
        )
        Balance.objects.create(user=self.user)

        self.user2 = User.objects.create_user(
            username='user2',
            first_name='testuser2',
            last_name='testuser2',
            email='user2@example.com',
            password='Test1234',
        )
        self.user2.token = str(
            Token.objects.get_or_create(user=self.user2)[0]
        )
        Balance.objects.create(user=self.user2)
         

    def test_create_user(self):
        regurl = reverse('customuser-list')
        userinfo = {
            "username":     "user123",
            "first_name":   "",
            "last_name":    "",
            "email":        "mail@example.com",
            "password":     "0P9O87U6Y"
        }
        res = self.client.post(regurl, userinfo)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        loginurl = reverse('login')
        res = self.client.post(loginurl, userinfo)

        self.client.credentials(HTTP_AUTHORIZATION='Token '
            + res.data['auth_token'])

        meurl = reverse('customuser-me')
        res = self.client.get(meurl)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_course_by_superuser(self):
        """
        Убедиться что суперпользователь может создать курс
        """
        url = reverse('courses-list')
        data = {
            'author': 'Ivanov I.I.',
            'title': 'Programming on Python',
            'start_date': timezone.now(),
            'price': 100
        }
        self.client.credentials(HTTP_AUTHORIZATION='Token '
            + self.superuser.token)

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Course.objects.count(), 1)
        self.assertEqual(Course.objects.get().title, 'Programming on Python')

    def test_fail_to_create_course_by_user(self):
        """
        Убедиться что пользователь не может создать курс
        """
        url = reverse('courses-list')
        data = {
            'author': 'Ivanov I.I.',
            'title': 'Programming on Python',
            'start_date': timezone.now(),
            'price': 100
        }
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.user.token)

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Course.objects.count(), 0)

    def test_subscribe_on_course(self):
        """
        Убедиться что пользователь может подписаться на курс
        """
        create_courses()
        count = Course.objects.count()

        crs = Course.objects.get(id=count)
        Subscription.objects.create(user=self.user2, course=crs)
        subs_before = Subscription.objects.count()

        url = reverse('courses-pay', kwargs={'pk':crs.id})
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.user.token)
        data = { }
        bonuses_before = self.user.balance.bonus_count
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Subscription.objects.count(), subs_before + 1)
        self.assertEqual(Balance.objects.get(user=self.user.id).bonus_count,
            (bonuses_before - crs.price))
        
        user = User.objects.get(id=self.user.id)
        user2 = User.objects.get(id=self.user2.id)
        self.assertNotEqual(user.groups_of_courses.all()[0], None)
        self.assertNotEqual(user2.groups_of_courses.all()[0], None)
        self.assertNotEqual(user.groups_of_courses.all()[0], user2.groups_of_courses.all()[0])
        pdb.set_trace()

    def test_fail_subscribe_on_non_existing_course(self):
        """
        Убедиться что пользователь не может подписаться на не существующий курс
        """
        create_courses()
        count = Course.objects.count()

        url = reverse('courses-pay', kwargs={'pk': count+1})
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.user.token)
        data = { }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Subscription.objects.count(), 0)

    def test_fail_subscribe_on_same_course_twice(self):
        """
        Убедиться что пользователь не может подписаться дважды на один курс
        """
        create_courses()

        count = Course.objects.count()
        self.assertEqual(count, 4)

        url = reverse('courses-pay', kwargs={'pk': count})
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.user.token)
        data = { }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Subscription.objects.count(), 1)

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Subscription.objects.count(), 1)
