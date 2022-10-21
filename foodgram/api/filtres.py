from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe
from users.models import User


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(
        field_name='name',
        lookup_expr='starts_with'
    )

    class Meta:
        model = Ingredient
        fields = ('name', 'measurement_unit')


class RecipeFilter(filters.FilterSet):
    name = filters.CharFilter(
        field_name='name',
    ) 
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug',)
    author = filters.ModelChoiceFilter(queryset=User.objects.all())

    class Meta:
        model = Recipe
        fields = (
            'name',
            'tags',
            'author',
        )
 