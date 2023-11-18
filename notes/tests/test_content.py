from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from notes.models import Note

User = get_user_model()


class TestContent(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username="Лев Толстой")
        cls.note = Note.objects.create(
            title="Заголовок", text="Текст",
            slug="note-slug", author=cls.author
        )
        cls.reader = User.objects.create(username="Читатель простой")

    def test_note_in_list(self):
        url = reverse("notes:list")
        self.client.force_login(self.author)
        response = self.client.get(url)
        object_list = response.context["object_list"]
        self.assertIn(self.note, object_list)

    def test_wrong_note_in_list(self):
        users_statuses = (
            (self.author, True),
            (self.reader, False),
        )
        for user, in_list in users_statuses:
            self.client.force_login(user)
            url = reverse("notes:list")
            response = self.client.get(url)
            object_list = response.context["object_list"]
            self.assertEqual((self.note in object_list), in_list)

    def test_authorized_client_has_form(self):
        urls = (
            ("notes:edit", (self.note.slug,)),
            ("notes:add", None),
        )
        for name, args in urls:
            url = reverse(name, args=args)
            self.client.force_login(self.author)
            response = self.client.get(url)
            self.assertIn("form", response.context)
