import django_filters
from django.contrib.auth import get_user_model
from rest_framework.filters import SearchFilter

from recipes.models import Recipe

User = get_user_model()


class IngredientSearchFilter(SearchFilter):
    search_param = 'name'


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
