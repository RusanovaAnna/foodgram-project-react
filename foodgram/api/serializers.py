from django.contrib.auth.tokens import default_token_generator
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.generics import get_object_or_404
#from users.serializers import UserSerializer
from recipes.models import Ingredient, Recipe, Tag, FavouriteRecipe


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'
        read_only_fields = '__all__',

class RecipeSerializer(serializers.ModelSerializer):
    #tags = TagSerializer(many=True, read_only=True)
    #author = UserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = '__all__'
        read_only_fields = (
            'is_favorite',
            'is_shopping_cart',
        )


class FavoriteRecipeSerializer(serializers.ModelSerializer):

    user = serializers.ReadOnlyField(source='user.id',)
    recipe = serializers.ReadOnlyField(source='recipe.id',)
    class Meta:
        model = FavouriteRecipe
        fields = ('user', 'recipes',)
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
