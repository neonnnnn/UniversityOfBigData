from discussion import views
from discussion.views import logger
from django.urls import path
from django.utils.translation import gettext_lazy as _  # noqa F401

from universityofbigdata.utils import access_recorded

app_name = "Discussion"

urlpatterns = [
    path(
        "discussion_competition/<int:pk>",
        access_recorded(logger, "discussion", _("議論ページ"))(
            views.DiscussionCompetitionView.as_view()
        ),
        name="discussion_competition",
    ),
    path(
        "discussion_post/<int:pk>",
        access_recorded(logger, "discussion_topic", _("議論トピックページ"))(
            views.DiscussionPostView.as_view()
        ),
        name="discussion_post",
    ),
]
