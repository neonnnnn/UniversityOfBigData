from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, path
from django.utils.translation import gettext_lazy as _  # noqa F401

""" -----------インポート------------"""
from authentication.views import logger, not_implemented, top
from django.conf import settings
from django.conf.urls.static import static

from universityofbigdata.utils import access_recorded

urlpatterns = i18n_patterns(
    path("", access_recorded(logger, "top", _("トップページ"))(top), name="top"),
    path(
        "not_implemented/",
        access_recorded(logger, "not_implemented", _("実装されていないページ"))(
            not_implemented
        ),
        name="not_implemented",
    ),
    path("admin_tool/", admin.site.urls, name="admin"),
    path("i18n/", include("django.conf.urls.i18n")),
    path("competitions/", include("competitions.urls")),
    path("accounts/", include("accounts.urls")),
    path("discussion/", include("discussion.urls")),
    path("management/", include("management.urls")),
    path("authentication/", include("authentication.urls")),
    path(
        "oauth/", include("social_django.urls", namespace="social")
    ),  # Social Django用
    path("logs/", include("log_viewer.urls")),
    #
)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

""" ----------------デバッグがTrueだった場合----------------------"""
# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
