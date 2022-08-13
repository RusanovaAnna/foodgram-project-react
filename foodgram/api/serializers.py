from django.core.exceptions import ValidationError
from django.db import transaction
from drf_extra_fields.fields import HybridImageField
from recipes.models import (FavoriteRecipe, Ingredient, IngredientList, Recipe,
                            Tag)
from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from users.models import User
from users.serializers import UserSerializer


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'
        read_only_fields = '__all__',


class IngredientSerializer(serializers.ModelSerializer):
    id = serializers.CharField()
    name = serializers.ReadOnlyField()
    measurement_unit = serializers.ReadOnlyField()

    class Meta:
        model = Ingredient
        fields = '__all__'
        read_only_fields = '__all__',


class IngredientListSerializer(serializers.HyperlinkedModelSerializer):
    amount = serializers.IntegerField(min_value=1)
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientList
        fields = [
            'id',
            'name',
            'measurement_unit',
            'amount'
        ]
        

class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientSerializer(
        many=True, source='ingredient_list',
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = HybridImageField()
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time',
        )

    def validate(self, data):
        ingredients = []
        for ingredient in data['ingredient_list']:
            if ingredient['ingredient']['id'] not in ingredients:
                ingredients.append(ingredient['ingredient']['id'])
            else:
                raise serializers.ValidationError(
                    'Ingredients must not be repeated')
        tags = []
        for tag in data["tags"]:
            if tag not in tags:
                tags.append(tag)
            else:
                raise serializers.ValidationError(
                    "Repeating tags are not allowed"
                )
        return data
    
    def create(self, validated_data):
        image = validated_data.pop('image')
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        with transaction.atomic():
            recipe = Recipe.objects.create(image=image,
                                           **validated_data)
        self.get_ingredients_tags(ingredients, tags, recipe)
        return recipe

    def get_ingredients_tags(self, ingredients, tags, recipe):
        self.get_ingredients(ingredients, recipe)
        self.get_tags(tags, recipe)

    def get_ingredients(self, ingredients, recipe):
        with transaction.atomic():
            for ingredient in ingredients:
                amount = ingredient.get('amount')
                if not amount:
                    amount = 0
                ingredient_amount = IngredientList.objects.create(
                    recipe=recipe,
                    ingredient_id=ingredient.get('id'),
                    amount=amount
                )
                ingredient_amount.save()

    def get_tags(self, tags, recipe):
        with transaction.atomic():
            for tag_id in tags:
                recipe_tag = Tag.objects.create(
                    recipe=recipe,
                    tag_id=tag_id,
                )
                recipe_tag.save()

    def update(self, instance, validated_data):
        update = {
            'image': None,
            'ingredients': None,
            'tags': None
        }
        for u in update:
            if u in validated_data:
                update[u] = validated_data.pop(u)

        if update['image']:
            instance.image = update['image']
        instance = super().update(instance, validated_data)

        self.update_igredients_tags(update['ingredients'],
                               update['tags'], instance)
        return instance

    def update_igredients_tags(self, ingredients, tags, recipe):
        method = self.context.get('request').method
        with transaction.atomic():
            if method == 'PATCH':
                if ingredients:
                    IngredientList.objects.filter(recipe=recipe).delete()
                    self.ingrs_create(ingredients, recipe)
                if tags:
                    Tag.objects.filter(recipe=recipe).delete()
                    self.tags_create(tags, recipe)
            else:
                IngredientList.objects.filter(recipe=recipe).delete()
                Tag.objects.filter(recipe=recipe).delete()
                self.get_ingredients_tags(ingredients, tags, recipe)

    def get_is_favorited(self, request,):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return FavoriteRecipe.objects.filter(
            id=request.user.id,
        ).exists()

    def get_is_in_shopping_cart(self, obj,):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return IngredientList.objects.filter(
            recipe=obj,
        ).exists()

    
class FavoriteRecipeSerializer(serializers.ModelSerializer):
    #recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = FavoriteRecipe
        fields = '__all__',   

    #def create(self,):
    #    user =  self.context['request'].user
    #    recipe_id = self.context.get('request').parser_context['kwargs']['id']
    #    recipe = get_object_or_404(Recipe, id=recipe_id)
    #    if FavoriteRecipe.objects.filter(user=user, favorite=recipe).exists(): #validate
    #        if self.context['request'].method in ['POST']:
    #            raise serializers.ValidationError(
    #                    'This recipe is already in favorites')
    #    return FavoriteRecipe.objects.create(user=user, favorite=recipe)

