from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from recipes.models import Follow
from users.models import User, UserProfile

from api.pagination import UserPagination
from .serializers import MeSerializer, UserSerializer
from rest_framework.generics import (ListCreateAPIView,RetrieveUpdateDestroyAPIView,)
from .permissions import IsOwnerProfileOrReadOnly
from .serializers import UserProfileSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = (UserSerializer,)
    lookup_field = ('username',)
    pagination_class = (UserPagination,)

    @action(detail=False,
            methods=['get', 'patch', ],
            permission_classes=(IsAuthenticated,))
    def me(self, request):
        user = get_object_or_404(User, username=request.user.username)
        if request.method == 'GET':
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        if request.method == 'PATCH':
            serializer = MeSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated],
        serializer_class=[]
    )
    def subscription(self, request, *args, **kwargs):
        user = request.user
        queryset = User.objects.filter(subscribers__subscriber=user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['get', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, *args, **kwargs):
        user = request.user
        author = get_object_or_404(User, id=kwargs['id'])
        subscription = Follow.objects.filter(
            subscriber=user,
            author=author
        )
        if (
            request.method == 'GET'
            and user != author
            and not subscription.exists()
        ):
            Follow.objects.create(
                subscriber=user,
                author=author
            )
            serializer = UserSerializer(
                author,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE' and subscription.exists():
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)


