from api.pagination import CustomPageNumberPagination
from recipes.models import Follow
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView, get_object_or_404
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import User

from .serializers import (FollowSerializer, MeSerializer,
                          SetPasswordSerializer, UserSerializer)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'id'
    permission_classes = [IsAuthenticatedOrReadOnly]

    @action(
        detail=False,
        methods=['get', 'patch', ],
        permission_classes=[IsAuthenticated, ],
        url_path='me',
        serializer_class=MeSerializer
    )
    def me(self, pk=None):
        serializer = self.get_serializer(self.request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

  #  @action(
  #      methods=['get'],
  #      detail=False,
  #      permission_classes=[IsAuthenticated],
  #      url_path='subscriptions',
  #      url_name='subscriptions',
  #  )
   # def subscription(self, request):
    #    user = request.user
     #   follows = Follow.objects.filter(user=user)
      #  page = self.paginate_queryset(follows)
       # if page is not None:
       #     serializer = FollowSerializer(page, many=True)
       #     return self.get_paginated_response(serializer.data)
       # serializer = FollowSerializer(follows, many=True)
       # return Response(serializer.data)

   # @action(
   #     detail=False,
   #     methods=['get', 'delete'],
   #     permission_classes=[IsAuthenticated],
   #     url_path=r'(?P<id>[\d]+)/subscribe',
   #     url_name='subscribe',
   #     pagination_class=None,
   # )
   # def subscribe(self, request, id):
    #    user = request.user
    #    author = get_object_or_404(User, id=id)
    #    subscription = Follow.objects.filter(
    #        user=user,
    #        author=author
    #    )
    #    if (
    #        request.method == 'GET'
    #        and not subscription.exists()
    #        and user != author
    #    ):
    #        Follow.objects.create(
    #            user=user,
    #            author=author
    #        )
    #        serializer = UserSerializer(
    #            author,
    #            context={'request': request}
    #        )
    #        return Response(serializer.data, status=status.HTTP_201_CREATED)
    #    if request.method == 'DELETE' and subscription.exists():
    #        subscription.delete()
    #        return Response(status=status.HTTP_204_NO_CONTENT)
     #   return Response(status=status.HTTP_400_BAD_REQUEST)

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

class FollowViewSet(APIView):
    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination

    def post(self, request, *args, **kwargs):
        user_id = self.kwargs.get('user_id')
        if user_id == request.user.id:
            return Response(
                {'error': 'You cant follow yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if Follow.objects.filter(
                user=request.user,
                author_id=user_id
        ).exists():
            return Response(
                {'error': 'You are already following a user'},
                status=status.HTTP_400_BAD_REQUEST
            )
        author = get_object_or_404(User, id=user_id)
        Follow.objects.create(
            user=request.user,
            author_id=user_id
        )
        return Response(
            self.serializer_class(author, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    def delete(self, request, *args, **kwargs):
        user_id = self.kwargs.get('user_id')
        get_object_or_404(User, id=user_id)
        subscription = Follow.objects.filter(
            user=request.user,
            author_id=user_id
        )
        if subscription:
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'error': 'You are not following a user'},
            status=status.HTTP_400_BAD_REQUEST
        )


class FollowListView(ListAPIView):
    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        return User.objects.filter(following__user=self.request.user)
