"""Page API views."""

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.permissions import CanReadPage
from apps.api.serializers import (
    CreatePageSerializer,
    DeletePageSerializer,
    EditPageSerializer,
    MovePageSerializer,
    PageSerializer,
    ProtectPageSerializer,
    RestorePageSerializer,
    RevisionBriefSerializer,
    RevisionSerializer,
)
from apps.core.exceptions import PermissionDenied
from apps.core.models.page import Page
from apps.core.selectors import get_page_for_read
from apps.core.services.moves import move_page
from apps.core.services.pages import (
    create_page,
    delete_page,
    edit_page,
    protect_page,
    restore_page,
)


class PageListCreateView(APIView):
    """List pages or create a new page."""

    serializer_class = PageSerializer

    @extend_schema(operation_id="api_pages_list", responses=PageSerializer(many=True))
    def get(self, request):
        """Return a paginated page list."""
        queryset = Page.objects.order_by("-updated_at")
        namespace = request.query_params.get("namespace")
        if namespace is not None:
            try:
                queryset = queryset.filter(namespace=int(namespace))
            except (TypeError, ValueError) as exc:
                raise ValidationError({"namespace": "This must be an integer"}) from exc

        privileged = (
            getattr(request.user, "is_superuser", False)
            or request.user.has_perm("core.delete_page")
            or request.user.has_perm("core.suppress_page")
        )
        deleted = request.query_params.get("is_deleted")
        if deleted is None:
            queryset = queryset.filter(is_deleted=False)
        else:
            requested_deleted = deleted.lower() in {"1", "true", "yes"}
            if requested_deleted and not privileged:
                raise PermissionDenied("You may not list deleted pages")
            queryset = queryset.filter(is_deleted=requested_deleted)
        if not privileged:
            queryset = queryset.filter(is_suppressed=False)

        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        return paginator.get_paginated_response(PageSerializer(page, many=True).data)

    def post(self, request):
        """Create a page and its first revision."""
        serializer = CreatePageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        page = create_page(
            title=data["title"],
            main_content=data["main"],
            author=request.user,
            properties=data.get("properties"),
            namespace=data.get("namespace", 0),
            comment=data.get("comment", ""),
        )
        return Response(PageSerializer(page).data, status=status.HTTP_201_CREATED)


class PageDetailView(APIView):
    """Read or soft-delete a page."""

    permission_classes = [CanReadPage]
    serializer_class = PageSerializer

    @extend_schema(operation_id="api_pages_retrieve", responses=PageSerializer)
    def get(self, request, page_id: int):
        """Return page metadata."""
        page = get_page_for_read(page_id)
        self.check_object_permissions(request, page)
        return Response(PageSerializer(page).data)

    def delete(self, request, page_id: int):
        """Soft-delete a page."""
        serializer = DeletePageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        delete_page(
            page_id=page_id,
            author=request.user,
            base_revid=serializer.validated_data["base_revid"],
            reason=serializer.validated_data.get("reason", ""),
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class PageEditView(APIView):
    """Create a new revision for a page."""

    serializer_class = EditPageSerializer

    def post(self, request, page_id: int):
        """Apply an edit with mandatory optimistic concurrency."""
        serializer = EditPageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        revision = edit_page(
            page_id=page_id,
            author=request.user,
            base_revid=data["base_revid"],
            main=data.get("main"),
            properties=data.get("properties"),
            comment=data.get("comment", ""),
            minor=data.get("minor", False),
            bot=data.get("bot", False),
        )
        return Response(RevisionSerializer(revision).data)


class PageRevisionsView(APIView):
    """Return a page's revision history."""

    permission_classes = [CanReadPage]
    serializer_class = RevisionBriefSerializer

    def get(self, request, page_id: int):
        """Return paginated revisions."""
        page = get_page_for_read(page_id)
        self.check_object_permissions(request, page)
        queryset = (
            page.revisions.select_related("author")
            .prefetch_related("slots__content")
            .order_by("-page_rev_number")
        )
        paginator = PageNumberPagination()
        revisions = paginator.paginate_queryset(queryset, request, view=self)
        return paginator.get_paginated_response(RevisionBriefSerializer(revisions, many=True).data)


class PageRestoreView(APIView):
    """Restore a soft-deleted page."""

    serializer_class = RestorePageSerializer

    def post(self, request, page_id: int):
        """Restore a page and rebuild its title bindings."""
        serializer = RestorePageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        page = restore_page(
            page_id=page_id,
            author=request.user,
            base_revid=serializer.validated_data["base_revid"],
            reason=serializer.validated_data.get("reason", ""),
        )
        return Response(PageSerializer(page).data)


class PageMoveView(APIView):
    """Move, rename or swap a page title."""

    serializer_class = MovePageSerializer

    def post(self, request, page_id: int):
        """Move a page to a new primary title."""
        serializer = MovePageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        result = move_page(
            page_id=page_id,
            new_title=data["new_title"],
            author=request.user,
            base_revid=data["base_revid"],
            reason=data.get("reason", ""),
            create_redirect=data.get("create_redirect", True),
            conflict_policy=data.get("conflict_policy", "fail"),
        )
        payload = {
            "page": PageSerializer(result.page).data,
            "revision": RevisionSerializer(result.revision).data,
            "old_primary": result.old_primary,
            "new_primary": result.new_primary,
            "redirect_page": (
                PageSerializer(result.redirect_page).data if result.redirect_page else None
            ),
            "target_page": (
                PageSerializer(result.target_page).data if result.target_page else None
            ),
            "target_revision": (
                RevisionSerializer(result.target_revision).data if result.target_revision else None
            ),
        }
        return Response(payload)


class PageProtectView(APIView):
    """Set a page's protection levels."""

    serializer_class = ProtectPageSerializer

    def post(self, request, page_id: int):
        """Update protection after checking the protect permission."""
        serializer = ProtectPageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        page = protect_page(
            page_id=page_id,
            author=request.user,
            protection=serializer.validated_data["protection"],
            base_revid=serializer.validated_data["base_revid"],
            reason=serializer.validated_data.get("reason", ""),
            expires_at=serializer.validated_data.get("expires_at"),
        )
        return Response(PageSerializer(page).data)
