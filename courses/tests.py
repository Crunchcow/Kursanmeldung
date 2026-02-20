from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from .models import Course, Registration
from django.utils import timezone


class CourseAccessTests(TestCase):
    def setUp(self):
        User = get_user_model()
        # two instructors (staff) so they can log into the admin site
        self.instructor1 = User.objects.create_user('inst1', 'inst1@example.com', 'pw')
        self.instructor1.is_staff = True
        self.instructor1.first_name = 'First'
        self.instructor1.last_name = 'Instructor'
        self.instructor1.save()
        self.instructor2 = User.objects.create_user('inst2', 'inst2@example.com', 'pw')
        self.instructor2.is_staff = True
        self.instructor2.save()
        self.course1 = Course.objects.create(
            name='Course 1',
            start_time=timezone.now().time(),
            end_time=timezone.now().time(),
            max_participants=1,
            price_member=10,
            price_non_member=20,
            instructor_user=self.instructor1,
        )
        self.course2 = Course.objects.create(
            name='Course 2',
            start_time=timezone.now().time(),
            end_time=timezone.now().time(),
            max_participants=1,
            price_member=10,
            price_non_member=20,
            instructor_user=self.instructor2,
        )
        # create group
        self.group = Group.objects.create(name='Kursleitung')
        self.instructor1.groups.add(self.group)
        self.instructor2.groups.add(self.group)

        # create registrations
        self.reg1 = Registration.objects.create(
            course=self.course1,
            first_name='Foo',
            last_name='Bar',
            email='foo@example.com',
            iban='DE000',
            account_holder='Foo Bar',
            terms_accepted=True,
        )
        self.reg2 = Registration.objects.create(
            course=self.course2,
            first_name='Baz',
            last_name='Qux',
            email='baz@example.com',
            iban='DE111',
            account_holder='Baz Qux',
            terms_accepted=True,
        )

    def test_kursleitung_sees_only_own_course(self):
        self.client.force_login(self.instructor1)
        # admin changelist view for courses
        response = self.client.get('/admin/courses/course/')
        self.assertContains(response, 'Course 1')
        self.assertNotContains(response, 'Course 2')

    def test_kursleitung_sees_only_own_registrations(self):
        self.client.force_login(self.instructor1)
        response = self.client.get('/admin/courses/registration/')
        self.assertContains(response, 'Foo')
        self.assertNotContains(response, 'Baz')

    def test_login_page_uses_card(self):
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'card-header')

    def test_course_register_page_card(self):
        # create a simple course to register for
        course = Course.objects.create(
            name='Test',
            start_time=timezone.now().time(),
            end_time=timezone.now().time(),
            max_participants=1,
            price_member=5,
            price_non_member=10,
        )
        response = self.client.get(f'/register/{course.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'card-header')

    def test_header_shows_username(self):
        user = get_user_model().objects.create_user('foo', 'foo@example.com', 'pw')
        user.is_staff = True
        user.first_name = 'Foo'
        user.last_name = 'Bar'
        user.save()
        self.client.force_login(user)
        response = self.client.get('/')
        self.assertContains(response, 'Angemeldet als')
        self.assertContains(response, 'Foo Bar')

    def test_course_list_uses_table(self):
        # add several courses to exercise table layout
        from datetime import date, timedelta
        today = date.today()
        for i in range(3):
            Course.objects.create(
                name=f'Course {i}',
                start_time=timezone.now().time(),
                end_time=timezone.now().time(),
                max_participants=10,
                price_member=10,
                price_non_member=20,
                start_date=today,
                end_date=today + timedelta(days=1),
            )
        response = self.client.get('/')
        self.assertContains(response, '<table', status_code=200)
        self.assertContains(response, '<th scope="col">Kurs</th>')
