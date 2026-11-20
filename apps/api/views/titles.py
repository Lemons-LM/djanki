"""Title resolution and history API views."""

from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.serializers import TitleBindingSerializer, TitleResolutionSerializer
from apps.core.models.title_binding import TitleBinding
from apps.core.permissions import require
from apps.core.selectors import title_binding_history
from apps.core.services.titles import resolve_title
from apps.core.titles import normalize_title


class TitleResolveView(APIView):
    """Resolve a title, alias or redirect."""

    serializer_class = TitleResolutionSerializer

    def get(self, request):
        """Return the canonical page and redirect chain for a title."""
        title = request.query_params.get("title")
        if not title:
            raise serializers.ValidationError({"title": "This query parameter is required"})
        try:
            namespace = int(request.query_params.get("namespace", 0))
        except (TypeError, ValueError) as exc:
            raise serializers.ValidationError({"namespace": "This must be an integer"}) from exc

        resolution = resolve_title(title, namespace)
        require(request.user, "read", resolution.page)
        return Response(
            TitleResolutionSerializer(
                {
                    "requested_title": resolution.requested.full_title,
                    "canonical_title": resolution.canonical_binding.display_title,
                    "page_id": resolution.page.pk,
                    "is_alias": resolution.is_alias,
                    "is_redirect": resolution.is_redirect,
                    "redirect_chain": resolution.redirect_chain,
                }
            ).data
        )


class TitleBindingsView(APIView):
    """Return active and historical title bindings."""

    serializer_class = TitleBindingSerializer

    def get(self, request):
        """Return all binding intervals for a title."""
        title = request.query_params.get("title")
        if not title:
            raise serializers.ValidationError({"title": "This query parameter is required"})
        try:
            namespace = int(request.query_params.get("namespace", 0))
        except (TypeError, ValueError) as exc:
            raise serializers.ValidationError({"namespace": "This must be an integer"}) from exc
        normalized = normalize_title(title, namespace)

        queryset = title_binding_history(normalized.key, namespace=normalized.namespace)
        privileged = (
            getattr(request.user, "is_superuser", False)
            or request.user.has_perm("core.delete_page")
            or request.user.has_perm("core.suppress_page")
        )
        if not privileged:
            queryset = queryset.filter(
                page__is_deleted=False,
                page__is_suppressed=False,
            )
        paginator = PageNumberPagination()
        bindings: list[TitleBinding] = (
            paginator.paginate_queryset(queryset, request, view=self) or []
        )
        return paginator.get_paginated_response(TitleBindingSerializer(bindings, many=True).data)
