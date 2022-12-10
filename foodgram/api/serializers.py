#from django.db import transaction
from django.db.models import F
from drf_extra_fields.fields import HybridImageField
from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from recipes.models import (FavoriteRecipe, Ingredient, IngredientList, Recipe,
                            Shop, Tag, TagInRecipe)
from users.models import User
from users.serializers import UserSerializer


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')
        read_only_fields = ('id', 'name', 'color', 'slug')


class TagInRecipeGetSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='tag.id')
    name = serializers.ReadOnlyField(source='tag.name')
    color = serializers.ReadOnlyField(source='tag.color')
    slug = serializers.ReadOnlyField(source='tag.slug')

    class Meta:
        model = TagInRecipe
        fields = ('id', 'name', 'color', 'slug')


class IngredientListSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient.id', queryset=Ingredient.objects.all()
    )
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
    )
    name = serializers.CharField(
        source='ingredient.name',
    )

    class Meta:
        model = IngredientList
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientRecipeGetSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientList
        fields = ('id', 'amount')


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
            and FavoriteRecipe.objects.filter(
                user=user,
                recipe__id=recipe_id
            ).exists()
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
            raise serializers.ValidationError('Recipe was not in favorites')
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

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeShortSerializer(
            instance.recipe, context=context).data


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = serializers.SerializerMethodField()
   # ingredients = IngredientSerializer(read_only=True, many=True)
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
        queryset = IngredientList.objects.filter(recipe=obj)
        return IngredientListSerializer(queryset, many=True).data

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
    
   # def get_ingredients(self, obj):
   #     recipe_ingredients = IngredientList.objects.filter(recipe=obj)
   #     return IngredientRecipeGetSerializer(
   #         recipe_ingredients,
   #         many=True
   #     ).data


class RecipeAddSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
  #  author = UserSerializer(read_only=True)
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
        read_only_fields = ('id', 'author', 'tags')

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
                    'This tag doesnt exist yet('
                )
    
  #  def add_ingredients(self, recipe, ingredients):
  #      for ingr in ingredients:
  #          IngredientList.objects.create(
  #              ingredient_id=ingr.get('id'),
  #              amount=ingr.get('amount'),
  #              recipe=recipe
  #          )
    
    def add_ingredients(self, ingredients, recipe):
        ingredient = []
        for ingredient in ingredients:
            ingredient.append(
                recipe=recipe,
                ingredient_id=self.ingredient.get('id'),
                amount=self.ingredient.get('amount')
            )
        IngredientList.objects.bulk_create(ingredient)
        return ingredient

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.add(tags)
        self.add_ingredients(recipe, ingredients)
        recipe.save()
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        super().update(instance, validated_data)
        instance.ingredients.clear()
        instance.tags.add(tags)
        self.add_ingredients(instance, ingredients)
        instance.save()
        return instance

    def to_representation(self, instance):
        serializer = RecipeSerializer(instance)
        return serializer.data

   # def create(self, validated_data):
   #     ingredients_data = validated_data.pop('ingredients')
   #     tags_data = validated_data.pop('tags')
   #     recipe = Recipe.objects.create(**validated_data)
   #     for ingredient in ingredients_data:
   #         amount = ingredient['amount']
   #         id = ingredient['id']
   #         IngredientRecipeGetSerializer.objects.create(
   #             ingredient=get_object_or_404(Ingredient, id=id),
   #             recipe=recipe, amount=amount
   #         )
   #     for tag in tags_data:
   #         recipe.tags.add(tag)
   #     return 

    #def update(self, instance, validated_data):
   #     ingredients_data = validated_data.pop('ingredients')
    #    tags_data = validated_data.pop('tags')
   #     instance.name = validated_data.get('name', instance.name)
   #     instance.text = validated_data.get('text', instance.text)
   #     instance.image = validated_data.get('image', instance.image)
   #     instance.cooking_time = validated_data.get(
   #         'cooking_time', instance.cooking_time
   #     )
   #     IngredientRecipeGetSerializer.objects.filter(recipe=instance).delete()
   #     for ingredient in ingredients_data:
   #         amount = ingredient['amount']
   #         id = ingredient['id']
   #         IngredientRecipeGetSerializer.objects.create(
   #             ingredient=get_object_or_404(Ingredient, id=id),
   #             recipe=instance, amount=amount
   #         )
   #     instance.save()
   #     instance.tags.set(tags_data)
    #    return instance
    
    #def to_representation(self, instance):
    #    data = RecipeSerializer(
    #        instance,
    #        context={'request': self.context.get('request')}
    #    ).data
    #    return data

    #def to_representation(self, instance):
    #    request = self.context.get('request')
    #    context = {'request': request}
    #    return RecipeShortSerializer(instance,
    #                                context=context).data
