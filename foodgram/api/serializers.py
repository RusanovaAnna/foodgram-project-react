from django.db import transaction
from drf_extra_fields.fields import HybridImageField
from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from users.serializers import UserSerializer
from recipes.models import *


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
    ingredients = serializers.SerializerMethodField()
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

    def get_ingredients(self, obj):
        recipe = obj
        queryset = recipe.ingredients.all()
        return IngredientSerializer(queryset, many=True).data
        

    def create(self, validated_data):
        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
        if 'tag' in validated_data:
            tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.add(*tags)
        self.add_ingredients(recipe, ingredients)
        return recipe
    

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        IngredientList.objects.filter(recipe=instance).delete()
        self.create_bulk(instance, ingredients_data)
        instance.name = validated_data.pop('name')
        instance.text = validated_data.pop('text')
        instance.cooking_time = validated_data.pop('cooking_time')
        if validated_data.get('image') is not None:
            instance.image = validated_data.pop('image')
        instance.save()
        instance.tags.set(tags_data)
        return instance
    
    def get_is_favorited(self, obj):
        return getattr(obj, 'is_favorited', False)

    def get_is_in_shopping_cart(self, obj):
        return getattr(obj, 'is_in_shopping_cart', False)


    
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

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.carts.filter(user=request.user).exists()

    def create(self,):
        user =  self.context['request'].user
        recipe_id = self.context.get('request').parser_context['kwargs']['id']
        recipe = get_object_or_404(Recipe, id=recipe_id)
        if FavoriteRecipe.objects.filter(user=user, recipe=recipe).exists():
            if self.context['request'].method in ['POST']:
                raise serializers.ValidationError(
                        'This recipe is already in favorites')
        return FavoriteRecipe.objects.create(user=user, recipe=recipe)

