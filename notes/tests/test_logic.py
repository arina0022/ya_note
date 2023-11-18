from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify


from notes.models import Note
from notes.forms import WARNING

User = get_user_model()


class TestLogic(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username="Лев Толстой")
        cls.note = Note.objects.create(
            title="Заголовок", text="Текст",
            slug="note-slug", author=cls.author
        )
        cls.url = reverse("notes:add")
        cls.reader = User.objects.create(username="Читатель простой")
        cls.form_data = {"title": "Название", "text": "Текстик"}
        cls.user = User.objects.create(username="Мимо Крокодил")
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)

    def test_anonymous_user_cant_create_notes(self):
        initial_notes_count = Note.objects.count()
        self.client.post(self.url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, initial_notes_count)

    def test_user_can_create_notes(self):
        initial_notes_count = Note.objects.count()
        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertRedirects(response, reverse("notes:success"))
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, initial_notes_count + 1)

    def test_not_unique_slug(self):
        initial_notes_count = Note.objects.count()
        url = reverse("notes:add")
        self.form_data["slug"] = self.note.slug
        response = self.auth_client.post(url, data=self.form_data)

        self.assertFormError(
            response, "form", "slug", errors=[self.note.slug + WARNING]
        )

        assert Note.objects.count() == initial_notes_count

    def test_empty_slug(self):
        initial_notes_count = Note.objects.count()
        url = reverse("notes:add")
        self.client.force_login(self.author)
        response = self.client.post(url, data=self.form_data)
        self.assertRedirects(response, reverse("notes:success"))
        assert Note.objects.count() == initial_notes_count + 1
        new_note = Note.objects.latest("id")
        expected_slug = slugify(self.form_data["title"])
        assert new_note.slug == expected_slug

    def test_user_cant_delete_note_of_another_user(self):
        initial_notes_count = Note.objects.count()
        url = reverse("notes:delete", args=(self.note.slug,))
        self.client.force_login(self.reader)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        comments_count = Note.objects.count()
        self.assertEqual(comments_count, initial_notes_count)

    def test_author_can_edit_note(self):

        url = reverse("notes:edit", args=(self.note.slug,))
        self.client.force_login(self.author)
        response = self.client.post(url, data=self.form_data)
        self.assertRedirects(response, reverse("notes:success"))
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.form_data["text"])

    def test_user_cant_edit_note_of_another_user(self):
        url = reverse("notes:edit", args=(self.note.slug,))
        self.client.force_login(self.reader)
        response = self.client.post(url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertNotEqual(self.note.text, self.form_data["text"])
