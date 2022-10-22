import django_filters
from recipes.models import Ingredient, Recipe
from users.models import User


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='starts_with'
    )

    class Meta:
        model = Ingredient
        fields = ('name', 'measurement_unit')


class RecipeFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name='name',
    )
    tags = django_filters.AllValuesMultipleFilter(field_name='tags__slug',)
    author = django_filters.ModelChoiceFilter(queryset=User.objects.all())

    class Meta:
        model = Recipe
        fields = (
            'name',
            'tags',
            'author',
        )
