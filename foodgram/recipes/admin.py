from django.contrib.admin import ModelAdmin, display, register, site
from django.utils.translation import gettext_lazy as _

from .models import FavouriteRecipe, IngredientList, Recipe, Tag


site.register(IngredientList)
site.register(FavouriteRecipe)


@register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ('name', 'color', 'slug')
    search_fields = ('name', 'slug')
    list_filter = ('name', 'color',)
    ordering = ('name',)


@register(Recipe)
class RecipeAdmin(ModelAdmin):
    list_display = (
        'author',
        'ingredients',
        'tags',
        'image',
        'name',
        'text',
        'cooking_time',
     #   'created_date',
      #  'get_favorites',
    )
    filter_horizontal = ('tags',)
    search_fields = ('author',)
    list_filter = (
        'author',
        'ingredients',
        'tags',
        'name',
        'cooking_time',
    )
    ordering = ('created_date', 'author')

    @display(description='tags')
    def get_tags(self, obj):
        get_tags = obj.list_tags()
        if get_tags:
            return list(get_tags)
        return None

    @display(description='added to favorites')
    def get_favorites(self, obj):
        get_fav = obj.in_favourites.count()
        if get_fav:
            return get_fav
        return None