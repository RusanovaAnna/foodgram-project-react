#from django.db.models import Sum
import datetime
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipes.models import FavoriteRecipe, Ingredient, Recipe, Shop, Tag, IngredientList
from .filtres import IngredientSearchFilter, RecipeFilter
from .pagination import CustomPageNumberPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (FavoriteRecipeSerializer, IngredientSerializer,
                          RecipeAddSerializer, RecipeSerializer,
                          RecipeShortSerializer, ShopSerializer, TagSerializer)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (AllowAny,)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related(
        'author'
    ).prefetch_related('ingredients').all()
    permission_classes = [IsAuthorOrReadOnly]
    serializer_class = RecipeSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        is_favorited = self.request.query_params.get('is_favorited')
        if is_favorited is not None and int(is_favorited) == 1:
            return Recipe.objects.filter(favorite__user=self.request.user)
        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart')
        if is_in_shopping_cart is not None and int(is_in_shopping_cart) == 1:
            return Recipe.objects.filter(purchases__user=self.request.user)
        return Recipe.objects.all()

    def get_serializer_class(self):
        if self.action == 'favorite':
            return FavoriteRecipeSerializer
        elif self.action == 'shopping_cart':
            return ShopSerializer
        elif self.request.method == 'POST' or self.request.method == 'PATCH':
            return RecipeAddSerializer
        return self.serializer_class

    def add_recipe(self, model, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = self.request.user
        if model.objects.filter(recipe=recipe, user=user).exists():
            return Response(
                {'errors': 'Recipe already added'},
                status=status.HTTP_400_BAD_REQUEST
            )
        model.objects.create(recipe=recipe, user=user)
        serializer = RecipeShortSerializer(recipe)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    def delete_recipe(self, model, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = self.request.user
        obj = get_object_or_404(model, recipe=recipe, user=user)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['POST', 'DELETE', 'GET'],
        permission_classes=[IsAuthenticated],
        url_name='favorite',
    )
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            return self.add_recipe(FavoriteRecipe, request, pk)
        else:
            return self.delete_recipe(FavoriteRecipe, request, pk)

    @action(
        detail=False,
        methods=['POST', 'DELETE', 'GET'],
        permission_classes=[IsAuthenticated],
        url_path=r'(?P<pk>[\d]+)/shopping_cart',
        url_name='shopping_cart',
    )
    def shopping_cart(self, request, pk):
        if request.method == 'POST':
            return self.add_recipe(Shop, request, pk)
        else:
            return self.delete_recipe(Shop, request, pk)

    @action(
        detail=False,
        methods=['get'],
        url_name='download_shopping_cart',
        url_path='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        user = request.user
        recipe_id = Shop.objects.filter(user=user).values('recipe')
        recipes = Recipe.objects.filter(pk__in=recipe_id)
        shop_recipe_dict = {}
        n = 0
        for recipe in recipes:
            n += 1
            ing_amounts = IngredientList.objects.filter(recipe=recipe)
            for ing in ing_amounts:
                if ing.ingredient.name in shop_recipe_dict:
                    shop_recipe_dict[ing.ingredient.name][0] += ing.amount
                else:
                    shop_recipe_dict[ing.ingredient.name] = [
                        ing.amount,
                        ing.ingredient.measurement_unit
                    ]
        time = datetime.datetime.now()
        time = time.strftime("%d-%m-%Y")
        shop_text = (
            f'FoodGram\nВыбрано рецептов на сайте: {n}\
            \n-------------------\n{time}\
            \nСписок покупок для Вас:\
            \n-------------------'
        )
        for key, value in shop_recipe_dict.items():
            shop_text += f'\n{key} ({value[1]}) - {str(value[0])}'
        return HttpResponse(shop_text, content_type='text/plain')


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = [IngredientSearchFilter]
    search_fields = ('^name',)
