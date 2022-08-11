from api.pagination import UserPagination
from djoser.serializers import SetPasswordSerializer
from recipes.models import Follow
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.models import User

from .serializers import *


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'id'
    pagination_class = UserPagination

    @action(detail=False,
            methods=['get', 'patch', ],
            permission_classes=[IsAuthenticated,],
            url_path='me',)
    def me(self, request, pk=None):
        serializer = self.get_serializer(self.request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='subscriptions',
        url_name='subscriptions',
    )
    def subscriptions(self, request):
        user = request.user
        follows = User.objects.filter(follower__following=user)
        page = self.paginate_queryset(follows)
        if page is not None:
            serializer = FollowSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = FollowSerializer(follows, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['get', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path=r'(?P<id>[\d]+)/subscribe',
        url_name='subscribe',
        pagination_class=None,
    )
    def subscribe(self, request, id=None):
        user = request.user
        obj = self.get_object()
        is_subscribed = Follow.objects.filter(
            following=user, follower=obj
        ).exists()
        if request.method == 'GET' and not is_subscribed:
            Follow.objects.create(following=user, follower=obj)
            serializer = self.get_serializer(obj)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE' and is_subscribed:
            Follow.objects.filter(following=user, follower=obj).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'Is not Authenticated'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(
        methods=['post'],
        detail=False,
        url_path='set_password',
        url_name='set_password',
        permission_classes=[IsAuthenticated],
    )
    def set_password(self, request,):
        user = request.user
        serializer = SetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if user.check_password(
            serializer.validated_data.get('current_password')
        ):
            user.set_password(serializer.validated_data.get('new_password'))
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'current_password': 'incorrect password'},
            status=status.HTTP_400_BAD_REQUEST
        )
    