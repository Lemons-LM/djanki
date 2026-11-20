"""User and block serializers."""

from rest_framework import serializers

from apps.user.models import Block


class BlockSerializer(serializers.ModelSerializer):
    """A block history row."""

    target_username = serializers.CharField(source="target.username", read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Block
        fields = [
            "id",
            "target",
            "target_username",
            "blocked_by",
            "blocked_by_name",
            "reason",
            "start_at",
            "expires_at",
            "unblocked_at",
            "unblocked_by_name",
            "unblock_reason",
            "autoblock",
            "no_create",
            "is_active",
            "created_at",
        ]


class BlockUserSerializer(serializers.Serializer):
    """Input for blocking a user."""

    reason = serializers.CharField(required=False, allow_blank=True, default="")
    expires_at = serializers.DateTimeField(required=False, allow_null=True, default=None)
    autoblock = serializers.BooleanField(required=False, default=False)
    no_create = serializers.BooleanField(required=False, default=False)


class UnblockUserSerializer(serializers.Serializer):
    """Input for unblocking a user."""

    reason = serializers.CharField(required=False, allow_blank=True, default="")
