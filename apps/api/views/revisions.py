"""Revision API views."""

from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.serializers import RevisionSerializer
from apps.core.permissions import require
from apps.core.services.revisions import get_revision_state, resolve_revision


class RevisionDetailView(APIView):
    """Look up a revision by global revid or readable slug."""

    serializer_class = RevisionSerializer

    def get(self, request, lookup: str):
        """Return a revision and its slot map."""
        revision = resolve_revision(lookup)
        require(request.user, "read", revision.page)
        return Response(RevisionSerializer(revision).data)


class RevisionSlotsView(APIView):
    """Return only the slot map for a revision."""

    serializer_class = RevisionSerializer

    def get(self, request, lookup: str):
        """Return each slot's content."""
        revision = resolve_revision(lookup)
        require(request.user, "read", revision.page)
        state = get_revision_state(revision)
        slots = {
            role: {
                "content_model": content.content_model,
                "content": content.as_json() if content.is_json else content.text,
            }
            for role, content in state.items()
        }
        return Response({"revid": revision.pk, "slug": revision.slug, "slots": slots})
