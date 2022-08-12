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


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientSerializer(
        many=True, source="ingredient_list"
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
        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.add(*tags)
        self.get_ingredients(recipe, ingredients)
        return recipe


    @staticmethod
    def get_ingredients(instance, ingredients):
        for ingredient in ingredients:
            Ingredient.objects.get_or_create(
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount'],
                recipe=instance
            )

    @transaction.atomic
    def update(self, instance, validated_data):
        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
            instance.tags.clear()
            instance.tags.add(*tags)
        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            Ingredient.objects.filter(recipe=instance).delete()
            self.get_ingredients(instance, ingredients)
        super().update(instance, validated_data)
        return instance

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        user = request.user
        return FavoriteRecipe.objects.filter(recipe=obj, user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        user = request.user
        return IngredientList.objects.filter(recipe=obj, user=user).exists()
    #def get_is_in_shopping_cart(self, obj): 
    #    return getattr(obj, 'is_in_shopping_cart', False) 

    
class FavoriteRecipeSerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = FavoriteRecipe
        fields = '__all__',   

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.is_favorited.filter(id=request.user.id).exists()

    #def get_is_in_shopping_cart(self, obj):
    #    request = self.context.get('request')
    #    if not request or not request.user.is_authenticated:
    #        return False
    #    return obj.ingredients_list.filter(user=request.user).exists()

    def create(self,):
        user =  self.context['request'].user
        recipe_id = self.context.get('request').parser_context['kwargs']['id']
        recipe = get_object_or_404(Recipe, id=recipe_id)
        if FavoriteRecipe.objects.filter(user=user, recipe=recipe).exists(): #validate
            if self.context['request'].method in ['POST']:
                raise serializers.ValidationError(
                        'This recipe is already in favorites')
        return FavoriteRecipe.objects.create(user=user, recipe=recipe)

