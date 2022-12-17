from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.models import Subscription, User
from .serializers import (SetPasswordSerializer, SubscriptionSerializer,
                          UserSerializer)


class UserViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'id'

    @action(
        detail=False,
        methods=['GET', 'PATCH', ],
        permission_classes=[IsAuthenticated, ],
        url_path='me',
    )
    def me(self, pk=None):
        serializer = self.get_serializer(self.request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        url_path='subscriptions',
        url_name='subscriptions',
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        user = request.user
        queryset = user.follower.all()
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        url_path='subscribe',
        url_name='subscribe',
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)
        if user == author:
            return Response(
                {'errors': 'You cant follow/unfollow yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )
        subscription = Subscription.objects.filter(
            author=author,
            user=user
        )
        if request.method == 'POST':
            if subscription.exists():
                return Response(
                    {'errors': 'Cant subscribe again'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            queryset = Subscription.objects.create(author=author, user=user)
            serializer = SubscriptionSerializer(
                queryset, context={'request': request})
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        if request.method == 'DELETE':
            if not subscription.exists():
                return Response(
                    {'errors': 'Cant unsubscribe again'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        methods=['POST'],
        detail=False,
        url_path='set_password',
        url_name='set_password',
        permission_classes=[IsAuthenticated],
        serializer_class=SetPasswordSerializer,
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
            {'current_password': 'Wrong password entered'},
            status=status.HTTP_400_BAD_REQUEST
        )
