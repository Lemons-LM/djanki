"""User block API views."""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.serializers.users import (
    BlockSerializer,
    BlockUserSerializer,
    UnblockUserSerializer,
)
from apps.user.exceptions import UserNotFound
from apps.user.models import Block
from apps.user.services.blocks import block_user, unblock_user

User = get_user_model()


def get_user_or_404(user_id: int):
    """Return a user or raise ``UserNotFound``."""
    try:
        return User.objects.get(pk=user_id)
    except User.DoesNotExist as exc:
        raise UserNotFound(details={"user_id": user_id}) from exc


class UserBlockView(APIView):
    """Block a user."""

    serializer_class = BlockUserSerializer

    def post(self, request, user_id: int):
        """Create a block after permission checks."""
        serializer = BlockUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        block = block_user(
            target=get_user_or_404(user_id),
            blocked_by=request.user,
            reason=data["reason"],
            expires_at=data.get("expires_at"),
            autoblock=data.get("autoblock", False),
            no_create=data.get("no_create", False),
        )
        return Response(BlockSerializer(block).data, status=status.HTTP_201_CREATED)


class UserUnblockView(APIView):
    """Lift all active blocks for a user."""

    serializer_class = UnblockUserSerializer

    def post(self, request, user_id: int):
        """Unblock a user and return the number of lifted blocks."""
        serializer = UnblockUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        count = unblock_user(
            target=get_user_or_404(user_id),
            unblocked_by=request.user,
            reason=serializer.validated_data.get("reason", ""),
        )
        return Response({"unblocked": count})


class UserBlocksView(APIView):
    """Return a user's block history."""

    serializer_class = BlockSerializer

    def get(self, request, user_id: int):
        """Return paginated block rows."""
        target = get_user_or_404(user_id)
        queryset = target.blocks.select_related("target", "blocked_by").order_by("-start_at", "-id")
        paginator = PageNumberPagination()
        blocks: list[Block] = paginator.paginate_queryset(queryset, request, view=self) or []
        return paginator.get_paginated_response(BlockSerializer(blocks, many=True).data)
