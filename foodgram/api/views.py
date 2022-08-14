from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import TokenCreateView
from requests import delete
from recipes.models import (FavoriteRecipe, Ingredient, IngredientList, Recipe,
                            Tag)
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from .filtres import IngredientFilter, RecipeFavoriteFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (FavoriteRecipeSerializer, IngredientListSerializer,
                          IngredientSerializer, RecipeSerializer,
                          ShopSerializer, TagSerializer, RecipeAddSerializers)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related(
        'author'
    ).prefetch_related('ingredients').all()
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly,]
    serializer_class = RecipeSerializer
    filterset_class = RecipeFilter
    

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
    

    def create_delete(self, model, serializer_model, request, pk):
        user = request.user
        recipe=get_object_or_404(Recipe, id=pk,)
        obj = model.objects.filter(recipe=recipe, user=user).exists()
        if request.method == 'POST' and not obj:
            model.objects.create(user=user, recipe=recipe)
            serializer = serializer_model(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE' and obj:
            obj = get_object_or_404(
                model, recipe=recipe, user=user
            )
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)


    @action(
        detail=True, 
        methods=['POST', 'DELETE', 'GET'], 
        permission_classes=[IsAuthenticated],
        url_name='favorite',
        filterset_class=RecipeFavoriteFilter,
    )
    def favorite(self, request, pk):
        return self.create_delete(
            FavoriteRecipe, FavoriteRecipeSerializer, request, pk
        )


    @action(
        detail=False,
        methods=['POST', 'DELETE', 'GET'],
        permission_classes=[IsAuthenticated],
        url_path=r'(?P<pk>[\d]+)/shopping_cart',
        url_name='shopping_cart',
    )
    def shopping_cart(self, request, pk):
        return self.create_delete(
            IngredientList, IngredientListSerializer, request, pk
        )
    

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
