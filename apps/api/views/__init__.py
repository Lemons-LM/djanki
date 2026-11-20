"""API views."""

from .pages import (
    PageDetailView,
    PageEditView,
    PageListCreateView,
    PageMoveView,
    PageProtectView,
    PageRestoreView,
    PageRevisionsView,
)
from .revisions import RevisionDetailView, RevisionSlotsView
from .titles import TitleBindingsView, TitleResolveView
from .users import UserBlockView, UserBlocksView, UserUnblockView

__all__ = [
    "PageDetailView",
    "PageEditView",
    "PageListCreateView",
    "PageMoveView",
    "PageProtectView",
    "PageRestoreView",
    "PageRevisionsView",
    "RevisionDetailView",
    "RevisionSlotsView",
    "TitleBindingsView",
    "TitleResolveView",
    "UserBlockView",
    "UserBlocksView",
    "UserUnblockView",
]
