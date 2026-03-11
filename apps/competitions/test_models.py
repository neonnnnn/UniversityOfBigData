"""Test models."""

import io
from time import sleep

import numpy as np
from competitions.management.commands.runapscheduler import setplan01
from competitions.models import (
    CompetitionModel,
    CompetitionPost,
)
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, TransactionTestCase
from django.utils import timezone


def _to_npz_bytes(values):
    buffer = io.BytesIO()
    np.savez(buffer, labels=np.asarray(values))
    return buffer.getvalue()


def _to_gt_npz_bytes(values, public_ratio=0.5):
    buffer = io.BytesIO()
    labels = np.asarray(values)
    n = len(labels)
    public_indices = np.arange(int(n * public_ratio))
    private_indices = np.arange(
        int(n * public_ratio), n
    )  # 公開データと非公開データのインデックスを分割
    np.savez(
        buffer,
        label=labels,
        public_indices=public_indices,
        private_indices=private_indices,
    )
    return buffer.getvalue()


def _make_npz_file(filename, values):
    return SimpleUploadedFile(filename, _to_npz_bytes(values))


def _make_gt_npz_file(filename, values, public_ratio=0.5):
    return SimpleUploadedFile(filename, _to_gt_npz_bytes(values, public_ratio))


def prepare_files(pred=[0, 1, 1], gt=[0, 1, 2]):
    # 提出ファイル例?
    desc_file = _make_npz_file("desc.npz", pred)
    # 正解ファイル
    gt_file = _make_gt_npz_file("gt.npz", gt)

    # 提出ファイル
    submission_file = _make_npz_file("pred.npz", pred)
    return desc_file, gt_file, submission_file


def launch_competition():
    # 提出例ファイル
    pred_file = _make_npz_file("example_pred.npz", [0])
    # 正解ファイル
    gt_file = _make_gt_npz_file("gt.npz", [0])

    CompetitionModel.objects.create(
        title="画像分類",
        title_en="Image Classification",
        competition_abstract="画像の分類精度を競います。",
        competition_description="画像を分類し、画像分類の評価指標により自動で評価を行います。",
        problem_type="classification",
        evaluation_type="accuracy",
        file_description="画像の正解ラベル",
        blob_key=pred_file,
        truth_blob_key=gt_file,
        open_datetime=timezone.make_aware(timezone.datetime(2023, 7, 11, 9, 0)),
        close_datetime=timezone.make_aware(timezone.datetime(2023, 7, 31, 18, 0)),
        status="active",
    )


class CompetitionModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        launch_competition()

    def test_title_label(self):
        """コンペのタイトルのフィールド名が想定通りか."""
        compe = CompetitionModel.objects.get(id=1)
        field_label = compe._meta.get_field("title").verbose_name
        self.assertEqual(field_label, "コンペティションのタイトル（日本語）")

    def test_owner_name_lost_if_None(self):
        """owner_nameが未設定の場合、owner lostが代入されているか."""
        compe = CompetitionModel.objects.get(id=1)
        self.assertEqual(compe.owner_name, "owner lost")


class CompetitionPostTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        launch_competition()
        compe = CompetitionModel.objects.get(id=1)
        submission_file = _make_npz_file("submission.npz", [0])
        CompetitionPost.objects.create(post=compe, post_key=submission_file)

    def test_count_posts_equals_1(self):
        """投稿数が1になっているか."""
        compe_post = CompetitionPost.objects.get(id=1)
        self.assertEqual(compe_post.count_posts, 1)
        self.assertEqual(compe_post.count_par_today, 1)

    def test_wrong_npz_posted(self):
        """XXX: 作成途中、不正なnpzデータが投稿された場合に例外処理されるか."""
        compe = CompetitionModel.objects.get(id=1)
        submission_file = SimpleUploadedFile("submission.npz", b"image")
        CompetitionPost.objects.create(post=compe, post_key=submission_file)


class StatusUpdateTests(TransactionTestCase):
    def test_comp_status_update(self):
        """コンペの状態更新がうまくできているか."""
        pred = np.arange(10)
        gt = np.arange(10)
        desc_file, gt_file, _ = prepare_files(pred, gt)

        # コンペティション作成
        title = "コンペの状態更新のテスト"
        comp = CompetitionModel.objects.create(
            title=title,
            title_en="A test of the scheduler",
            competition_abstract="スケジューラのテストです。",
            competition_description="スケジューラのテストです。",
            problem_type="classification",
            evaluation_type="accuracy",
            file_description="ファイルの説明欄",
            blob_key=desc_file,
            truth_blob_key=gt_file,
            open_datetime=timezone.now() + timezone.timedelta(seconds=3),
            close_datetime=timezone.now() + timezone.timedelta(seconds=6),
            status="coming",
        )
        setplan01()

        self.assertEqual(comp.status, "coming")

        sleep(4)
        setplan01()

        comp = CompetitionModel.objects.get(title=title)
        self.assertEqual(comp.status, "active")

        sleep(4)
        setplan01()

        comp = CompetitionModel.objects.get(title=title)
        self.assertEqual(comp.status, "completed")
