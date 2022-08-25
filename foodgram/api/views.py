from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import TokenCreateView
from recipes.models import FavoriteRecipe, Ingredient, Recipe, Shop, Tag
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.validators import ValidationError

from .filtres import IngredientFilter, RecipeFavoriteFilter, RecipeFilter
from .pagination import RecipePagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (FavoriteRecipeSerializer, IngredientSerializer,
                          RecipeAddSerializers, RecipeSerializer,
                          RecipeShortSerializer, ShopSerializer, TagSerializer)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related(
        'author'
    ).prefetch_related('ingredients').all()
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly, ]
    serializer_class = RecipeSerializer
    filterset_class = RecipeFilter
    pagination_class = RecipePagination

    def get_serializer_class(self):
        if self.action == 'favorite':
            return FavoriteRecipeSerializer
        elif self.action == 'shopping_cart':
            return ShopSerializer
        return self.serializer_class

    @action(
        detail=True,
        serializer_class=RecipeAddSerializers,
    )
    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(author=user)

    def add_recipe(self, model, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = self.request.user
        if model.objects.filter(recipe=recipe, user=user).exists():
            raise ValidationError('Recipe already added')
        model.objects.create(recipe=recipe, user=user)
        serializer = RecipeShortSerializer(recipe)
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
        filterset_class=RecipeFavoriteFilter,
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
        in_cart = Recipe.objects.filter(author=user)
        queryset = in_cart.values_list(
            'ingredients__name',
            'ingredients__measurement_unit',
        ).annotate(
            amount_sum=Sum('ingredient_list__amount')
        )
        text = 'Список покупок для вас: \n'
        for ingredient in queryset:
            text += (
                f"{list(ingredient)[0]} - "
                f"{list(ingredient)[2]} "
                f"{list(ingredient)[1]} \n"
            )
        response = HttpResponse(text, 'Content-Type: application/txt')
        response['Content-Disposition'] = 'attachment; filename="yourwishlist"'
        return response


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    filterset_class = IngredientFilter
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name', )


class CustomTokenCreateView(TokenCreateView):

    def _action(self, serializer):
        response = super()._action(serializer)
        response.status_code = status.HTTP_201_CREATED
        return response
