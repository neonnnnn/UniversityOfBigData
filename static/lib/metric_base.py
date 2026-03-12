# -*- coding: utf-8 -*-

import abc
import logging
from abc import abstractmethod
from numbers import Real
from typing import Any, List, Tuple, TypeVar, Union

import numpy as np
import sklearn.metrics
from django.utils.translation import gettext_lazy as _  # noqa F401

T = TypeVar("T")
Array = Union[List[T], np.ndarray[T]]
logger = logging.getLogger(__name__)


class MetricBase(abc.ABC):
    greater_is_better = True

    def __init__(self, public_lb_ratio: Real, *args, **kwargs):
        self.public_lb_ratio = public_lb_ratio

    @abstractmethod
    def __call__(
        self, gt_file: str, submitted_file: str, *args, **kwargs
    ) -> Tuple[Real, Real]:
        pass


class NPZReaderMixin:
    @staticmethod
    def _normalize_sample_shape(data: np.ndarray) -> np.ndarray:
        # Keep compatibility with previous behavior while supporting image-like
        # tensors: (N, H, W) -> (N, H*W).
        if data.ndim == 0:
            return data.reshape(1, 1)
        if data.ndim == 1:
            return data.reshape(-1, 1)
        if data.ndim == 3:
            return data.reshape(data.shape[0], -1)
        return data

    def read_gt_file(
        self,
        file_path: Any,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Read a GT NPZ file with keys: label, public_indices, private_indices."""
        if hasattr(file_path, "seek"):
            file_path.seek(0)

        required_keys = {"label", "public_indices", "private_indices"}
        with np.load(file_path, allow_pickle=False) as npz_data:
            if not required_keys.issubset(set(npz_data.files)):
                raise RuntimeError(
                    "Invalid gt npz format: must contain keys "
                    "'label', 'public_indices', 'private_indices'"
                )
            labels = np.asarray(npz_data["label"])
            public_indices = np.asarray(npz_data["public_indices"])
            private_indices = np.asarray(npz_data["private_indices"])

        all_indices = np.concatenate([public_indices, private_indices])
        if len(all_indices) != len(labels):
            raise RuntimeError(
                "Invalid gt npz: len(public_indices) + len(private_indices) "
                f"({len(all_indices)}) != len(label) ({len(labels)})"
            )
        if len(np.unique(all_indices)) != len(all_indices):
            raise RuntimeError(
                "Invalid gt npz: public_indices and private_indices must not overlap"
            )

        labels = self._normalize_sample_shape(labels)
        return labels, public_indices, private_indices

    def read_pred_file(
        self,
        file_path: Any,
    ) -> np.ndarray:
        """Read a submission NPZ file with a single key."""
        if hasattr(file_path, "seek"):
            file_path.seek(0)

        with np.load(file_path, allow_pickle=False) as npz_data:
            if len(npz_data.files) != 1:
                raise RuntimeError("Invalid npz format")
            data = np.asarray(npz_data[npz_data.files[0]])

        return self._normalize_sample_shape(data)

    # Backward-compat alias
    read_file = read_pred_file


class NPZSubmissionMetric(MetricBase, NPZReaderMixin):
    @abstractmethod
    def metric_fn(self, y_gt: Array, y_pred: Array, *args, **kwargs):
        pass

    def __call__(self, gt_file: str, submitted_file: str, *args, **kwargs):
        y_gt, public_indices, private_indices = self.read_gt_file(gt_file)
        y_pred = self.read_pred_file(submitted_file)

        if len(y_pred) != len(y_gt):
            raise RuntimeError("Invalid sample size")

        score_pub = self.metric_fn(
            y_gt[public_indices], y_pred[public_indices], *args, **kwargs
        )
        score_priv = self.metric_fn(
            y_gt[private_indices], y_pred[private_indices], *args, **kwargs
        )

        return score_pub, score_priv


class MSE(NPZSubmissionMetric):
    name = "mean_squared_error"
    display_name = _("二乗平均誤差")
    greater_is_better = False

    def metric_fn(self, y_gt: Array, y_pred: Array, *args, **kwargs):
        return sklearn.metrics.mean_squared_error(y_gt, y_pred, *args, **kwargs)


class MAE(NPZSubmissionMetric):
    name = "mean_absolute_error"
    display_name = _("平均絶対誤差")
    greater_is_better = False

    def metric_fn(self, y_gt: Array, y_pred: Array, *args, **kwargs):
        return sklearn.metrics.mean_absolute_error(y_gt, y_pred, *args, **kwargs)


class RMSE(NPZSubmissionMetric):
    name = "root_mean_squared_error"
    display_name = _("二乗平均平方根誤差")
    greater_is_better = False

    def metric_fn(self, y_gt: Array, y_pred: Array, *args, **kwargs):
        return np.sqrt(
            sklearn.metrics.mean_squared_error(y_gt, y_pred, *args, **kwargs)
        )


class ROCAUC(NPZSubmissionMetric):
    name = "roc_auc_score"
    display_name = _("Area under the ROC curve (AUC)")
    greater_is_better = True

    def metric_fn(self, y_gt: Array, y_pred: Array, *args, **kwargs):
        return sklearn.metrics.roc_auc_score(y_gt.astype(int), y_pred, *args, **kwargs)


class Accuracy(NPZSubmissionMetric):
    name = "accuracy"
    display_name = _("正解率")
    greater_is_better = True

    def metric_fn(self, y_gt: Array, y_pred: Array, *args, **kwargs):
        return sklearn.metrics.accuracy_score(y_gt, y_pred, *args, **kwargs)


class Recall(NPZSubmissionMetric):
    name = "recall"
    display_name = _("適合率")
    greater_is_better = True

    def metric_fn(self, y_gt: Array, y_pred: Array, average="macro", *args, **kwargs):
        return sklearn.metrics.recall_score(
            y_gt, y_pred, average=average, *args, **kwargs
        )


class Precision(NPZSubmissionMetric):
    name = "precision"
    display_name = _("再現率")
    greater_is_better = True

    def metric_fn(self, y_gt: Array, y_pred: Array, average="macro", *args, **kwargs):
        return sklearn.metrics.precision_score(
            y_gt, y_pred, average=average, *args, **kwargs
        )


class F1(NPZSubmissionMetric):
    name = "f1"
    display_name = _("f値")
    greater_is_better = True

    def metric_fn(self, y_gt: Array, y_pred: Array, average="macro", *args, **kwargs):
        return sklearn.metrics.f1_score(y_gt, y_pred, average=average, *args, **kwargs)


class ExactMatchRatio(NPZSubmissionMetric):
    name = "exact_match_ratio"
    display_name = _("Exact Match Ratio")
    greater_is_better = True

    def metric_fn(self, y_gt: Array, y_pred: Array, *args, **kwargs):
        return (y_gt == y_pred).all(1).mean()


# Backward compatibility for custom user-defined metrics.
CSVSubmissionMetric = NPZSubmissionMetric
