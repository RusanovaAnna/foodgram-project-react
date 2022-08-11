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

    @staticmethod
    def add_or_delete(request, serializer, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method != 'POST':
            get_object_or_404(
                Recipe,
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

    def update(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=False,
        methods=['get', 'delete'],
        permission_classes=[IsAuthenticated],
        filterset_class=RecipeFavoriteFilter,
        url_name='favorite',
        url_path=r'(?P<id>[\d]+)/favorite',
        serializer_class=FavoriteRecipe,
    )
    def favorite(self, request,):
        user = request.user
        obj = self.get_object()
        fav = FavoriteRecipe.objects.filter(user=user, favorite=obj).exists()
        if request.method == 'GET' and not fav:
            FavoriteRecipe.objects.create(user=user, favorite=obj)
            serializer = self.get_serializer(obj)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE' and fav:
            FavoriteRecipe.objects.filter(user=user, favorite=obj).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'Is not Authenticated'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    @action(
        detail=False,
        methods=['get', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path=r'(?P<id>[\d]+)/shopping_cart',
        url_name='shopping_cart',
    )
    def shopping_cart(self, request,):
        user = request.user
        obj = self.get_object()
        in_cart = IngredientList.objects.filter(customer=user, cart=obj).exists()
        if request.method == 'GET' and not in_cart:
            IngredientList.objects.create(customer=user, cart=obj)
            serializer = self.get_serializer(obj)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE' and in_cart:
            IngredientList.objects.filter(customer=user, cart=obj).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'error': 'Is not Authenticated.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(
        detail=False,
        methods=['get'],
        url_name='download_shopping_cart',
        url_path='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        user = request.user
        in_cart = Recipe.objects.filter(ingredient_list__customer=user)
        queryset = in_cart.values_list(
            'ingredients__name',
            'ingredients__measurement_unit',
        ).annotate(
            amount_sum=Sum('ingredients__amount')
        )
        text = 'Список покупок: \n'
        for ingredient in queryset:
            text += (
                f"{list(ingredient)[0]} - "
                f"{list(ingredient)[2]} "
                f"{list(ingredient)[1]} \n"
            )
        response = HttpResponse(text, 'Content-Type: application/txt')
        response['Content-Disposition'] = 'attachment; filename="wishlist"'
        return response


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    filterset_class = IngredientFilter
    serializer_class = IngredientSerializer
    pagination_class = None
    

class CreateTokenView(TokenCreateView):

    def _action(self, serializer):
        response = super()._action(serializer)
        response.status_code = status.HTTP_201_CREATED
        return response
