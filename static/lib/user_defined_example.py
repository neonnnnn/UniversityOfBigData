"""My custom metric."""

from django.utils.translation import gettext_lazy as _

from .metric_base import CSVSubmissionMetric


class MyMetric(CSVSubmissionMetric):
    name = "my_metric"
    display_name = _("カスタム指標")

    def metric_fn(self, y_gt, y_pred, *args, **kwargs):
        return (y_gt * y_pred).sum()


metrics = {
    "my_metric": MyMetric,
}
