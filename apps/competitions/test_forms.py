"""Test forms."""

import io

import numpy as np
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils.translation import gettext_lazy as _  # noqa F401

from .forms import (
    CompetitionPostCreateForm,
)

User = get_user_model()


def _to_npz_bytes(values):
    buffer = io.BytesIO()
    np.savez(buffer, labels=np.asarray(values))
    return buffer.getvalue()


class CompetitionPostCreateFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="test_user",
            email="test@test",
        )

    def test_ValidationError_filename_not_endswith_npz(self):
        """clean_post_keyで拡張子が.npzでない場合にエラーを出すか."""
        submission_file = SimpleUploadedFile("pred.txt", b"dummy")
        data = {"count_par_today": 0}
        file_data = {"post_key": submission_file}
        form = CompetitionPostCreateForm(data, file_data, instance=self.user)

        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error("post_key"))
        self.assertEqual(form.errors["post_key"], [_("拡張子はnpzのみです")])

    def test_filename_endswith_npz(self):
        """clean_post_keyで拡張子が.npzになっている場合にvalidか."""
        submission_file = SimpleUploadedFile("pred.npz", _to_npz_bytes([0, 1, 1]))
        data = {"count_par_today": 0}
        file_data = {"post_key": submission_file}
        form = CompetitionPostCreateForm(data, file_data, instance=self.user)

        self.assertTrue(form.is_valid())
        self.assertFalse(form.has_error("post_key"))
