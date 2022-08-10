from turtle import color
from django_filters import rest_framework as filters
from recipes.models import FavouriteRecipe


class RecipeFilter(filters.FilterSet):
    name = filters.CharFilter(
        field_name='name',
    )
    is_favorited = filters.NumberFilter(
        method='favourite',
    )
    is_in_shopping_cart = filters.NumberFilter(
        method='shopping_cart',
    )
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug',)

    def get_is_favorited(self, queryset, value, name):
        if value and not self.request.user.is_anonymous:
            return queryset.filter(favorited__user=self.request.user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, value, name):
        if value and not self.request.user.is_anonymous:
            return queryset.filter(user_shopping_cart__user=self.request.user)
        return queryset

    class Meta:
        model = FavouriteRecipe
        fields = (
            'user',
            'tags',
        )