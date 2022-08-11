from django.contrib.auth.tokens import default_token_generator
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from users.serializers import UserSerializer
from recipes.models import *


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'
        read_only_fields = '__all__',

class RecipeSerializer(serializers.ModelSerializer):
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = '__all__'

    def get_ingredients(self, obj):
        return obj.ingredients.values(
            'id', 'name', 'measurement_unit',
        )

    def create(self, validated_data):
        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.add(*tags)
        self.add_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            IngredientList.objects.filter(recipe=instance).delete()
            self.add_ingredients(instance, ingredients)
        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
            instance.tags.clear()
            instance.tags.add(*tags)
        super().update(instance, validated_data)
        return instance
    
    def bool_response(self, request_obj, main_obj):
        request = self.context.get('request')
        user = request.user
        if request is None or request.user.is_anonymous:
            return False
        return main_obj.objects.filter(
            user=user, 
            recipe=request_obj.id
        ).exists()
    
    def get_is_favorited(self, obj):
        return self.bool_response(obj, FavouriteRecipe)
    
    def get_is_in_shopping_cart(self, obj):
        return self.bool_response(obj, IngredientList)

    
class FavouriteRecipeSerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = FavouriteRecipe
        fields = '__all__',   

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.is_favorited.filter(id=request.user.id).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.carts.filter(user=request.user).exists()

    def create(self,):
        user =  self.context['request'].user
        recipe_id = self.context.get('request').parser_context['kwargs']['id']
        recipe = get_object_or_404(Recipe, id=recipe_id)
        if FavouriteRecipe.objects.filter(user=user, recipe=recipe).exists():
            if self.context['request'].method in ['POST']:
                raise serializers.ValidationError(
                        'This recipe is already in favorites')
        return FavouriteRecipe.objects.create(user=user, recipe=recipe)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'
        read_only_fields = '__all__',
