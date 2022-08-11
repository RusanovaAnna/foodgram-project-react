from api.pagination import UserPagination
from django.shortcuts import get_object_or_404
from djoser.serializers import SetPasswordSerializer
from drf_yasg.utils import swagger_auto_schema
from recipes.models import Follow
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
#from rest_framework.views import APIView

from users.models import User

from .serializers import *

#from rest_framework.generics import (ListCreateAPIView,RetrieveUpdateDestroyAPIView,)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'id'
    pagination_class = UserPagination

    @action(detail=False,
            methods=['get', 'patch', ],
            permission_classes=[IsAuthenticated,],
            url_path='me',)
    #def me(self, request):
     #   user = get_object_or_404(User, username=request.user)
     #   if request.method == 'GET':
     #       serializer = UserSerializer(user)
     #       return Response(serializer.data, status=status.HTTP_200_OK)
     #   if request.method == 'PATCH':
     #       serializer = MeSerializer(user, data=request.data, partial=True)
    #        serializer.is_valid(raise_exception=True)
   #         serializer.save()
  #      return Response(serializer.data, status=status.HTTP_200_OK)
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
        queryset = Follow.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=['get', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path=r'(?P<id>[\d]+)/subscribe',
        url_name='subscribe',
        pagination_class=None,
    )
    def subscribe(self, request, **kwargs):
        user = request.user
        author = get_object_or_404(User, id=kwargs['id'])
        subscription = Follow.objects.filter(
            author=author,
            user=user,
        )
        if (request.method == 'GET'
            and user != author
            and not subscription.exists()):
            Follow.objects.create(
                user=user,
                author=author,
            )
            serializer = UserSerializer(
                author,
                context={'request': request},
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE' and subscription.exists():
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

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
    