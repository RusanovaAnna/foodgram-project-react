from ast import Delete
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models import Avg
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework_simplejwt.tokens import AccessToken
from foodgram.recipes.models import IngredientList

from recipes.models import Tag, Recipe, FavouriteRecipe, Follow, Ingredient
from users.models import User

from foodgram.settings import EMAIL_ADMIN

from .filtres import RecipeFilter
#from .mixins import ListCreateDestroyViewSet
from .pagination import UserPagination
from .permissions import (IsAdmin, IsAdminAuthorOrReadOnly,
                          IsAdminOrReadOnly)
from .serializers import (FavoriteRecipeSerializer, GetConfirmationCode,
                          GetTokenSerializer, RecipeFollowSerializer, RecipeSerializer,
                          TagSerializer,
                          UserSerializer, MeSerializer)


@api_view(['POST'])
@permission_classes([AllowAny],)
def get_confirmation_code(request):
    serializer = GetConfirmationCode(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    username = serializer.validated_data.get('username')
    user = get_object_or_404(User, username=username)
    confirmation_code = default_token_generator.make_token(user)
    send_mail(
        'Title: Please, use it code for generate token',
        f'{confirmation_code}',
        EMAIL_ADMIN,
        [serializer.validated_data['email']],
        fail_silently=False,
    )
    return Response(serializer.validated_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny],)
def get_token(request):
    serializer = GetTokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = get_object_or_404(
        User, username=serializer.validated_data.get('username'))
    token = AccessToken.for_user(user)
    return Response({'token': str(token)}, status=status.HTTP_200_OK)


class MyUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = UserSerializer
    lookup_field = 'username'
    pagination_class = UserPagination

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
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request):
        user = self.request.user
        author_id = self.kwargs['pk']
        author = get_object_or_404(User, id=author_id)
        following = Follow.objects.create(user=user, author=author)
        data = UserSerializer(following)
        return Response(data=data)
    
    @action(methods=['delete'])
    def delete_subscribe(self,):
        user = self.request.user
        author_id = self.kwargs['pk']
        author = get_object_or_404(User, id=author_id)
        if user != author:
        Follow.objects.filter(
            user=user,
            author=author,
        ).delete()


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    filter_backends = (RecipeFilter,)
    serializer_class = (RecipeSerializer,)
    permission_classes = (IsAdminAuthorOrReadOnly,)

    @action(
        methods=['post'],
        serializer_class=FavoriteRecipeSerializer,
    )
    def add_in_favourite(self,):
        user = self.request.user
        recipe = FavouriteRecipe.objects.create()
    
    @action(
        methods=['delete'],
        serializer_class=FavoriteRecipeSerializer,
    )
    def delete_favourite(self,):
        user = self.request.user
        recipe = FavouriteRecipe.objects.delete()


class IngredientsViewSet(viewsets.ModelViewSet):

    #@action(methods=['post'],)
    #def add_to_shopping_cart(self,):

    #@action(methods=['delete'],)
    #def delete_to_shopping_cart(self,):

    @action(methods=['get'])
    def get_wishlist(request):
        user = request.user
        wish_filter = IngredientList.objects.filter(
            user_id=user.id).values_list("recipe", flat=True)
        ingredient_filter = Ingredient.objects.filter(
            recipe_id__in=wish_filter).order_by('ingredient')
        ingredients = {}
        for ingredient in ingredient_filter:
            if ingredient.ingredient in ingredients.keys():
                ingredients[ingredient.ingredient] += ingredient.amount
            else:
                ingredients[ingredient.ingredient] = ingredient.amount

        wishlist = []
        for k, m in ingredients.items():
            wishlist.append(f'{k.title} - {m} {k.dimension} \n')
        wishlist.append('\n\n\n\n')
        wishlist.append('foodgram')

        response = HttpResponse(wishlist, 'Content-Type: text/plain')
        response['Content-Disposition'] = 'attachment; filename="wishlist.txt"'
        return response


#class APIChange_Password(APIView):
#    def post(self, request, *args, **kwargs):
#        serializer = PasswordSerializer(data=request.data)
#        if serializer.is_valid():
#            data = request.data
#            password = data['current_password'] 
#            user = User.objects.get(password=password)
#            if not user.check_password(serializer.data.get('current_password')):
#                return Response({'current_password': ['Wrong password.']}, 
#                                status=status.HTTP_400_BAD_REQUEST)
#            user.set_password(serializer.data.get('new_password'))
#            user.save()
#            return Response({'status': 'password set'}, status=status.HTTP_200_OK)
#
#        return Response(serializer.errors, 
#                        status=status.HTTP_400_BAD_REQUEST)