"""Revision and slot serializers."""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.core.models.revision import Revision


class RevisionBriefSerializer(serializers.ModelSerializer):
    """Summary of a revision without its content."""

    revid = serializers.IntegerField(source="id", read_only=True)
    slug = serializers.CharField(read_only=True)
    parent_revid = serializers.IntegerField(
        source="parent_revision_id", read_only=True, allow_null=True
    )
    author = serializers.CharField(source="author_name", read_only=True)

    class Meta:
        model = Revision
        fields = [
            "revid",
            "slug",
            "page_id",
            "page_rev_number",
            "parent_revid",
            "author",
            "comment",
            "created_at",
            "minor",
            "bot",
            "deleted",
            "suppressed",
        ]


class RevisionSerializer(RevisionBriefSerializer):
    """A revision including its full slot map."""

    slots = serializers.SerializerMethodField()

    class Meta(RevisionBriefSerializer.Meta):
        fields = RevisionBriefSerializer.Meta.fields + ["slots"]

    @extend_schema_field(serializers.DictField(child=serializers.DictField()))
    def get_slots(self, obj):
        """Return each slot's content, parsed for JSON and raw for text."""
        slots = {}
        for slot in obj.slots.select_related("content"):
            content = slot.content
            slots[slot.role] = {
                "content_model": content.content_model,
                "content": content.as_json() if content.is_json else content.text,
            }
        return slots
