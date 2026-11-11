from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from .models import Task


class TaskOwnershipTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='task-owner', password='test-password')
        self.other_user = User.objects.create_user(username='other-owner', password='test-password')
        self.client.force_login(self.user)

    def test_tasks_page_only_shows_current_users_tasks(self):
        own_task = Task.objects.create(title='My task', user=self.user)
        Task.objects.create(title='Another user task', user=self.other_user)

        response = self.client.get(reverse('tasks'))

        self.assertContains(response, own_task.title)
        self.assertNotContains(response, 'Another user task')

    def test_create_task_saves_it_for_current_user(self):
        response = self.client.post(
            reverse('create_task'),
            {'title': 'New task', 'description': 'Task details', 'important': 'on'},
        )

        self.assertRedirects(response, reverse('tasks'))
        task = Task.objects.get(title='New task')
        self.assertEqual(task.user, self.user)

    def test_create_task_page_loads(self):
        response = self.client.get(reverse('create_task'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create task')

    def test_invalid_create_task_submission_renders_form(self):
        response = self.client.post(reverse('create_task'), {})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create task')
        self.assertFormError(response.context['form'], 'title', 'This field is required.')

    def test_task_detail_shows_current_users_task(self):
        task = Task.objects.create(title='My task', user=self.user)

        response = self.client.get(reverse('task_detail', args=[task.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, task.title)

    def test_task_detail_hides_another_users_task(self):
        task = Task.objects.create(title='Another user task', user=self.other_user)

        response = self.client.get(reverse('task_detail', args=[task.pk]))

        self.assertEqual(response.status_code, 404)

    def test_task_detail_requires_login(self):
        task = Task.objects.create(title='My task', user=self.user)
        self.client.logout()

        response = self.client.get(reverse('task_detail', args=[task.pk]))

        self.assertRedirects(
            response,
            f'{reverse("login")}?next={reverse("task_detail", args=[task.pk])}',
        )

    def test_completing_task_marks_it_completed(self):
        task = Task.objects.create(title='Finished task', user=self.user)

        response = self.client.post(reverse('complete_task', args=[task.pk]))

        self.assertRedirects(response, reverse('tasks'))
        task.refresh_from_db()
        self.assertIsNotNone(task.datecompleted)
        self.assertContains(self.client.get(reverse('tasks')), '&#10003;')

    def test_uncompleted_task_does_not_show_check(self):
        Task.objects.create(title='Pending task', user=self.user)

        response = self.client.get(reverse('tasks'))

        self.assertNotContains(response, '&#10003;')

    def test_completing_another_users_task_returns_not_found(self):
        task = Task.objects.create(title='Another user task', user=self.other_user)

        response = self.client.post(reverse('complete_task', args=[task.pk]))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Task.objects.filter(pk=task.pk).exists())

    def test_completing_task_requires_post(self):
        task = Task.objects.create(title='Finished task', user=self.user)

        response = self.client.get(reverse('complete_task', args=[task.pk]))

        self.assertEqual(response.status_code, 405)
        self.assertTrue(Task.objects.filter(pk=task.pk).exists())
