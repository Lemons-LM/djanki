"""API v1 URL configuration."""

from django.urls import path

from apps.api.views import (
    PageDetailView,
    PageEditView,
    PageListCreateView,
    PageMoveView,
    PageProtectView,
    PageRestoreView,
    PageRevisionsView,
    RevisionDetailView,
    RevisionSlotsView,
    TitleBindingsView,
    TitleResolveView,
    UserBlockView,
    UserBlocksView,
    UserUnblockView,
)

urlpatterns = [
    path("pages/", PageListCreateView.as_view(), name="api-page-list"),
    path("pages/<int:page_id>/", PageDetailView.as_view(), name="api-page-detail"),
    path("pages/<int:page_id>/edit", PageEditView.as_view(), name="api-page-edit"),
    path(
        "pages/<int:page_id>/revisions/",
        PageRevisionsView.as_view(),
        name="api-page-revisions",
    ),
    path(
        "pages/<int:page_id>/restore",
        PageRestoreView.as_view(),
        name="api-page-restore",
    ),
    path("pages/<int:page_id>/move", PageMoveView.as_view(), name="api-page-move"),
    path(
        "pages/<int:page_id>/protect",
        PageProtectView.as_view(),
        name="api-page-protect",
    ),
    path(
        "revisions/<str:lookup>/",
        RevisionDetailView.as_view(),
        name="api-revision-detail",
    ),
    path(
        "revisions/<str:lookup>/slots/",
        RevisionSlotsView.as_view(),
        name="api-revision-slots",
    ),
    path("titles/bindings/", TitleBindingsView.as_view(), name="api-title-bindings"),
    path("titles/", TitleResolveView.as_view(), name="api-title-resolve"),
    path(
        "users/<int:user_id>/block",
        UserBlockView.as_view(),
        name="api-user-block",
    ),
    path(
        "users/<int:user_id>/unblock",
        UserUnblockView.as_view(),
        name="api-user-unblock",
    ),
    path(
        "users/<int:user_id>/blocks/",
        UserBlocksView.as_view(),
        name="api-user-blocks",
    ),
]
