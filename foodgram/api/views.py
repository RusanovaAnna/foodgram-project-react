from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import TokenCreateView
from rest_framework import status, viewsets, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

from recipes.models import Tag, Recipe, Ingredient, IngredientList, FavouriteRecipe
from users.models import User
from users.serializers import UserSerializer

from foodgram.settings import EMAIL_ADMIN

from .filtres import *
#from .mixins import ListCreateDestroyViewSet
from .permissions import (IsAuthorOrReadOnly,)
from .serializers import *


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related('author').prefetch_related(
        'ingredients'
    ).all()
    filterset_class = RecipeFilter
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly,]

    @staticmethod
    def add_or_delete(request, model, serializer, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method != 'POST':
            get_object_or_404(
                model,
                user=request.user,
                recipe=recipe,
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = serializer(
            data={'user': request.user.id, 'recipe': pk},
            context={'request': request},)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


    @action(
        detail=False,
        methods=['get', 'delete'],
        permission_classes=[IsAuthenticated],
        serializer_class=(FavouriteRecipeSerializer),
        filterset_class=RecipeFauvariteFilter,
        url_name='favorite',
        url_path=r'(?P<id>[\d]+)/favorite',
    )
    def favorite(self, request, **kwargs):
        user = request.user
        recipes = get_object_or_404(FavouriteRecipe, id=kwargs['id'])
        fav = User.objects.filter(
            id=user.id,
            favourite_recipe=recipes
        ).exists()
        if request.method == 'GET' and not fav:
            recipes.favorite.add(user)
            serializer = UserSerializer(recipes)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE' and fav:
            recipes.favorite.remove(user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)
    
    @action(
        detail=False,
        methods=['get', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='shopping_cart',
        url_name='shopping_cart',
    )
    def shopping_cart(self, request, **kwargs):
        user = request.user
        recipes = get_object_or_404(FavouriteRecipe, id=kwargs['id'])
        add = User.objects.filter(
            recipes=recipes,
            id=user.id,
        ).exists()
        if request.method == 'DELETE' and add:
            user.cart.recipes.remove(recipes)
            return Response(status=status.HTTP_204_NO_CONTENT)
        if request.method == 'GET' and not add:
            user.cart.recipes.add(recipes)
            serializer = UserSerializer(recipes)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['get'],
        url_name='download_shopping_cart',
        url_path='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        ingredients = (
            IngredientList.objects
            .select_related('ingredient', 'recipe')
            .prefetch_related('purchases')
            .filter(recipe__ingredients__user=request.user)
            .values_list('ingredient__name', 'ingredient__measurement_unit')
            .annotate(amount=sum('amount'))
        )

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = ('attachment;'
                                           'filename="Your_shopping_list.csv"')
        return response



class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    filterset_class = IngredientFilter
    serializer_class = IngredientSerializer
    pagination_class = None
    


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

class CreateTokenView(TokenCreateView):

    def _action(self, serializer):
        response = super()._action(serializer)
        response.status_code = status.HTTP_201_CREATED
        return response
