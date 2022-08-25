from django.db import transaction
from drf_extra_fields.fields import HybridImageField
from recipes.models import (FavoriteRecipe, Ingredient, IngredientList, Recipe,
                            Shop, Tag, TagInRecipe)
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


class TagInRecipeGetSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='tag.id')
    name = serializers.ReadOnlyField(source='tag.name')
    color = serializers.ReadOnlyField(source='tag.color')
    slug = serializers.ReadOnlyField(source='tag.slug')

    class Meta:
        model = TagInRecipe
        fields = ('id', 'name', 'color', 'slug')


class IngredientListSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(source='ingredient'
                                                 '.measurement_unit')

    class Meta:
        model = IngredientList
        fields = [
            'id',
            'name',
            'measurement_unit',
            'amount',
        ]


class RecipeShortSerializer(serializers.ModelSerializer):
    image = HybridImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'cooking_time')


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = FavoriteRecipe
        fields = ('user', 'recipe')

    def validate(self, data):
        user = self.context.get('request').user
        recipe_id = data['recipe'].id
        if (
            self.context.get('request').method == 'GET'
            and FavoriteRecipe.objects.filter(user=user,
            recipe__id=recipe_id).exists()
        ):
            raise serializers.ValidationError(
                'Recipe already added to favorites')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        if (
            self.context.get('request').method == 'DELETE'
            and not FavoriteRecipe.objects.filter(
                user=user,
                recipe=recipe
            ).exists()
        ):
            raise serializers.ValidationError()
        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeShortSerializer(
            instance.recipe, context=context
        ).data


class ShopSerializer(FavoriteRecipeSerializer):

    class Meta(FavoriteRecipeSerializer.Meta):
        model = Shop


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientSerializer(
        many=True, source='ingredient_list',
        read_only=True,
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = HybridImageField()
    tags = TagInRecipeGetSerializer(read_only=True, many=True,
                                    source='recipe_tag')
    author = UserSerializer(read_only=True)
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time',
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return FavoriteRecipe.objects.filter(
            recipe=obj,
            user=request.user
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Shop.objects.filter(
            recipe=obj,
            user=request.user
        ).exists()


class RecipeAddSerializers(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=TagInRecipe.objects.all(),
        many=True
    )
    ingredients = IngredientListSerializer(many=True)
    image = HybridImageField()
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'name',
            'ingredients',
            'image',
            'text',
            'cooking_time'
        )

    def to_representation(self, instance):
        return RecipeSerializer(
            instance,
            context={
                'request': self.context.get('request')
            }
        ).data

    def validate(self, data):
        ingredients = data['ingredients']
        if not ingredients:
            raise serializers.ValidationError(
                'Ingredient must be added)'
            )
        unique_ingredients = []
        for ingredient in ingredients:
            name = ingredient['id']
            if int(ingredient['amount']) <= 0:
                raise serializers.ValidationError(
                    'Is the quantity value exactly greater than 0?'
                )
            if not isinstance(ingredient['amount'], int):
                raise serializers.ValidationError(
                    'Ingredient quantity must be a number'
                )
            if name not in unique_ingredients:
                unique_ingredients.append(name)
            else:
                raise serializers.ValidationError(
                    'Ingredient should not be repeated))'
                )
        return data

    def validate_cooking_time(self, data):
        if data <= 0:
            raise serializers.ValidationError(
                'Cooking time must not be less than 1 minute'
            )
        return data

    def tag_validate(self, tags):
        if not tags:
            raise serializers.ValidationError(
                'Tag must be added)'
            )
        if len(tags) > len(set(tags)):
            raise serializers.ValidationError(
                'Tags shoud be unique)'
            )
        for tag_id in tags:
            if not Tag.objects.filter(id=tag_id).exists():
                raise serializers.ValidationError(
                    'This tag doesnt exist yet{'
                )

    def create_ingredients(self, ingredients, recipe):
        for ingredient in ingredients:
            amount = ingredient['amount']
            ingredient = ingredient['id']
            ingredients, IngredientList.objects.get_or_create(
                recipe=recipe,
                ingredient=ingredient,
                amount=amount
            )

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        recipe.save()
        self.create_ingredients(ingredients, recipe)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.ingredients.clear()
        self.create_ingredients(ingredients, instance)
        instance.tags.clear()
        instance.tags.set(tags)
        return super().update(instance, validated_data)
