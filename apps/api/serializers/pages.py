"""Page API serializers."""

from rest_framework import serializers

from apps.core.models.page import Page
from apps.core.models.protection import PageProtection

from .revisions import RevisionBriefSerializer


class ProtectionSerializer(serializers.ModelSerializer):
    """An active structured page protection."""

    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = PageProtection
        fields = [
            "id",
            "action",
            "level",
            "expires_at",
            "set_by",
            "set_by_name",
            "set_at",
            "reason",
            "is_active",
        ]


class PageSerializer(serializers.ModelSerializer):
    """Page metadata and current revision summary."""

    title = serializers.CharField(source="primary_title", read_only=True)
    title_key = serializers.CharField(source="canonical_title_key", read_only=True)
    current_revision = RevisionBriefSerializer(read_only=True)
    is_redirect = serializers.BooleanField(read_only=True)
    redirect_target = serializers.IntegerField(source="redirect_target_id", read_only=True)
    protection = serializers.SerializerMethodField()
    protections = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()

    class Meta:
        model = Page
        fields = [
            "id",
            "namespace",
            "title",
            "title_key",
            "is_redirect",
            "redirect_target",
            "protection",
            "protections",
            "categories",
            "is_deleted",
            "is_suppressed",
            "current_revision",
            "revision_count",
            "created_at",
            "updated_at",
        ]

    def get_protection(self, obj) -> dict:
        """Return a simple ``action -> level`` map for active protections."""
        return {
            protection.action: protection.level
            for protection in obj.protections.all()
            if protection.is_active
        }

    def get_protections(self, obj) -> list:
        """Return full active protection rows."""
        active = [protection for protection in obj.protections.all() if protection.is_active]
        return list(ProtectionSerializer(active, many=True).data)

    def get_categories(self, obj) -> list:
        """Return the page's active category titles."""
        return [
            binding.full_title for binding in obj.category_bindings.filter(released_at__isnull=True)
        ]


class CreatePageSerializer(serializers.Serializer):
    """Input for creating a page and its first revision."""

    title = serializers.CharField(max_length=255)
    namespace = serializers.IntegerField(required=False, default=0)
    main = serializers.CharField(allow_blank=True)
    properties = serializers.JSONField(required=False)
    comment = serializers.CharField(required=False, allow_blank=True, default="")


class EditPageSerializer(serializers.Serializer):
    """Input for creating a new revision."""

    base_revid = serializers.IntegerField()
    main = serializers.CharField(required=False, allow_blank=True)
    properties = serializers.JSONField(required=False)
    comment = serializers.CharField(required=False, allow_blank=True, default="")
    minor = serializers.BooleanField(required=False, default=False)
    bot = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        """Require at least one changed slot."""
        if "main" not in attrs and "properties" not in attrs:
            raise serializers.ValidationError("Provide main, properties, or both")
        return attrs


class DeletePageSerializer(serializers.Serializer):
    """Input for soft-deleting a page."""

    base_revid = serializers.IntegerField()
    reason = serializers.CharField(required=False, allow_blank=True, default="")


class RestorePageSerializer(serializers.Serializer):
    """Input for restoring a page."""

    base_revid = serializers.IntegerField()
    reason = serializers.CharField(required=False, allow_blank=True, default="")


class MovePageSerializer(serializers.Serializer):
    """Input for renaming or swapping a page title."""

    base_revid = serializers.IntegerField()
    new_title = serializers.CharField(max_length=255)
    reason = serializers.CharField(required=False, allow_blank=True, default="")
    create_redirect = serializers.BooleanField(required=False, default=True)
    conflict_policy = serializers.ChoiceField(
        choices=["fail", "swap"], required=False, default="fail"
    )


class ProtectPageSerializer(serializers.Serializer):
    """Input for setting page protection."""

    base_revid = serializers.IntegerField()
    protection = serializers.JSONField()
    reason = serializers.CharField(required=False, allow_blank=True, default="")
    expires_at = serializers.DateTimeField(required=False, allow_null=True, default=None)
