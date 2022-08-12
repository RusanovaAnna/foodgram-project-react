from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import TokenCreateView
from recipes.models import *
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from .filtres import *
from .permissions import IsAuthorOrReadOnly
from .serializers import *


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

    #@staticmethod
    #@action(
     #   detail=False,
     #   methods=['post', 'delete'],
     #   permission_classes=[IsAuthenticated],
     #   serializer_class=RecipeSerializer,
    #)
    #def create(self, serializer, request, id=None):
        #if request.method != 'POST':
        #    serializer.delete(author=self.request.user)
        #    return Response(status=status.HTTP_204_NO_CONTENT)
        #serializer.save(author=self.request.user)
        #return Response(serializer.data, status=status.HTTP_201_CREATED)
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def update(self, serializer, id=None):
        serializer.save(author=self.request.user)
    
    def favorite_post_delete(self, related_manager, id=None):
        recipe = self.get_object()
        if self.request.method == 'DELETE':
            related_manager.get(recipe_id=recipe.id).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        if related_manager.filter(recipe=recipe).exists():
            raise ValidationError('Рецепт уже в избранном')
        related_manager.create(recipe=recipe)
        serializer = RecipeSerializer(instance=recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True,
            permission_classes=[IsAuthenticated],
            methods=['POST', 'DELETE'], )
    def favorite(self, request, id=None):
        return self.favorite_post_delete(
            request.user.favorite
        )
    #@action(
    #    detail=False,
    #    methods=['get', 'delete'],
    #    permission_classes=[IsAuthenticated],
    #    filterset_class=RecipeFavoriteFilter,
    #    url_name='favorite',
    #    url_path=r'(?P<id>[\d]+)/favorite',
    #    serializer_class=FavoriteRecipeSerializer,
    #)
    #def favorite(self, request, id):
    #    user = request.user
    #    model = FavoriteRecipe.objects.filter(user=user, recipe__id=id).exists()
    #    if request.method == 'GET' and not model:
    #        recipe=get_object_or_404(Recipe, id=id)
    #        FavoriteRecipe.objects.create(user=user, recipe=recipe)
    #        serializer = FavoriteRecipeSerializer(recipe)
    #        return Response(serializer.data, status=status.HTTP_201_CREATED)
    #    if request.method == 'DELETE' and model:
    #        FavoriteRecipe.objects.filter(user=user, recipe__id=id).delete()
     #       return Response(status=status.HTTP_204_NO_CONTENT)
     #   return Response(status=status.HTTP_400_BAD_REQUEST)
    
    @action(
        detail=False,
        methods=['get', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path=r'(?P<id>[\d]+)/shopping_cart',
        url_name='shopping_cart',
    )
    def shopping_cart(self, request, id):
        in_cart = IngredientList.objects.filter(recipe__id=id).exists()
        if request.method == 'POST' and not in_cart:
            recipe=get_object_or_404(Recipe, id=id)
            IngredientList.objects.create(recipe__id=id)
            serializer = RecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE' and in_cart:
            IngredientList.objects.filter(recipe__id=id).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

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
        text = 'Список покупок: \n'
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
    

class CustomTokenCreateView(TokenCreateView):

    def _action(self, serializer):
        response = super()._action(serializer)
        response.status_code = status.HTTP_201_CREATED
        return response
