from turtle import color
from django_filters import rest_framework as filters
from recipes.models import FavoriteRecipe, Recipe


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(
        field_name='name', lookup_expr='starts_with'
    )


class RecipeFavoriteFilter(filters.FilterSet):
    user = filters.CharFilter(
        field_name='user',
    )
    is_favorited = filters.NumberFilter(
        method='favourite',
    )
    is_in_shopping_cart = filters.NumberFilter(
        method='shopping_cart',
    )

    def get_is_favorited(self, queryset, value, name):
        if value and not self.request.user.is_anonymous:
            return queryset.filter(favorited__user=self.request.user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, value, name):
        if value and not self.request.user.is_anonymous:
            return queryset.filter(user_shopping_cart__user=self.request.user)
        return queryset

    class Meta:
        model = FavoriteRecipe
        fields = (
            'user',
        )


class RecipeFilter(filters.FilterSet):
    name = filters.CharFilter(
        field_name='name',
    )
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug',)


    class Meta:
        model = Recipe
        fields = (
            'name',
            'tags',
        )