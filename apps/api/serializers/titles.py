"""Title resolution and binding serializers."""

from rest_framework import serializers

from apps.core.models.title_binding import TitleBinding


class TitleBindingSerializer(serializers.ModelSerializer):
    """A title binding interval."""

    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = TitleBinding
        fields = [
            "id",
            "page_id",
            "namespace",
            "display_title",
            "normalized_title",
            "is_primary",
            "created_revision",
            "released_revision",
            "created_at",
            "released_at",
            "is_active",
        ]


class TitleResolutionSerializer(serializers.Serializer):
    """Result of resolving a title, alias or redirect."""

    requested_title = serializers.CharField()
    canonical_title = serializers.CharField()
    page_id = serializers.IntegerField()
    is_alias = serializers.BooleanField()
    is_redirect = serializers.BooleanField()
    redirect_chain = serializers.ListField(child=serializers.IntegerField())
