from django.contrib import admin
from django.contrib.admin import ModelAdmin, display

from .models import (FavoriteRecipe, Ingredient, IngredientList, Recipe, Tag, TagInRecipe)

admin.site.register(Recipe)
admin.site.register(Tag)
admin.site.register(Ingredient)
admin.site.register(FavoriteRecipe)


class TagAdmin(ModelAdmin):
    list_display = ('name', 'color', 'slug',)
    search_fields = ('name', 'slug',)
    list_filter = ('name', 'color',)
    ordering = ('name',)


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)
    empty_value_display = '-'


class IngredientInRecipeAdmin(admin.TabularInline):
    model = IngredientList
    extra = 1


class TagInRecipeAdmin(admin.StackedInline):
    model = TagInRecipe
    extra = 2


class RecipeAdmin(ModelAdmin):
    list_display = (
        'author', 'ingredients',
        'tags', 'image', 'name',
        'text', 'cooking_time',
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
    ordering = ('author')
    inlines = [IngredientInRecipeAdmin, TagInRecipeAdmin]

    @display(description='tags')
    def get_tags(self, obj):
        get_tags = obj.list_tags()
        if get_tags:
            return list(get_tags)
        return None

    @display(description='added to favorites')
    def favorite(self, obj):
        return obj.favorite_recipe.count()


@admin.register(IngredientList)
class IngredientInRAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    list_filter = ('recipe__name',)
    search_fields = ('recipe__name',)

@admin.register(TagInRecipe)
class TagInRAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'tag')
    list_filter = ('recipe__name',)
    search_fields = ('recipe__name',)
