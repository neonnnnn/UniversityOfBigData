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
    def read_file(
        self,
        file_path: Any,
    ) -> np.ndarray:
        if hasattr(file_path, "seek"):
            file_path.seek(0)

        with np.load(file_path, allow_pickle=False) as npz_data:
            if len(npz_data.files) != 1:
                raise RuntimeError("Invalid npz format")
            data = np.asarray(npz_data[npz_data.files[0]])

        # Keep compatibility with the previous CSV loader shape (N, 1)
        # when the source data is one-dimensional.
        if data.ndim == 0:
            return data.reshape(1, 1)
        if data.ndim == 1:
            return data.reshape(-1, 1)
        return data


class DataSplitterMixin:
    def split(
        self, data_gt: Array[Any], data_pred: Array[Any], ratio: Real
    ) -> Tuple[Array[Any], Array[Any]]:
        idx = int(len(data_gt) * ratio)
        return data_gt[:idx], data_pred[:idx]


class NPZSubmissionMetric(MetricBase, NPZReaderMixin, DataSplitterMixin):
    @abstractmethod
    def metric_fn(self, y_gt: Array, y_pred: Array, *args, **kwargs):
        pass

    def __call__(self, gt_file: str, submitted_file: str, *args, **kwargs):
        y_gt = self.read_file(gt_file)
        y_pred = self.read_file(submitted_file)

        if len(y_pred) != len(y_gt):
            raise RuntimeError("Invalid sample size")

        y_gt_pub, y_pred_pub = self.split(y_gt, y_pred, self.public_lb_ratio)

        score_pub = self.metric_fn(y_gt_pub, y_pred_pub, *args, **kwargs)
        score_priv = self.metric_fn(y_gt, y_pred, *args, **kwargs)

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
