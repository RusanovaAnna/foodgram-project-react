from django.db import transaction 
from drf_extra_fields.fields import HybridImageField
from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from recipes.models import (FavoriteRecipe, Ingredient, IngredientList, Recipe,
                            Shop, Tag, TagInRecipe)
from users.models import User
from users.serializers import UserSerializer


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'color',
            'slug'
        )
        lookup_field = 'id'
        extra_kwargs = {'url': {'lookup_field': 'id'}}



class TagInRecipeGetSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='tag.id')
    name = serializers.ReadOnlyField(source='tag.name')
    color = serializers.ReadOnlyField(source='tag.color')
    slug = serializers.ReadOnlyField(source='tag.slug')

    class Meta:
        model = TagInRecipe
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'
        read_only_fields = '__all__',


class IngredientListSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        read_only=True
    )
    name = serializers.SlugRelatedField(
        slug_field='name',
        source='ingredient',
        read_only=True
    )
    measurement_unit = serializers.SlugRelatedField(
        slug_field='measurement_unit',
        source='ingredient',
        read_only=True
    )

    class Meta:
        model = IngredientList
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    image = HybridImageField()
    cooking_time = serializers.IntegerField()
   # tags = TagSerializer(many=True, read_only=True)
    tags = TagSerializer(read_only=True, many=True)
    ingredients = serializers.SerializerMethodField()
    #tags = TagInRecipeGetSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    #ingredients = serializers.SerializerMethodField(read_only=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = '__all__'

   # def get_ingredients(self, obj):
   #     queryset = IngredientList.objects.filter(recipe=obj)
   #     return IngredientListSerializer(queryset, many=True).data
    def get_ingredients(self, obj):
        recipe = obj
        queryset = IngredientList.objects.filter(recipe=obj)
      #  queryset = recipe.recipes_ingredients_list.all()
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


class AddIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = IngredientList
        fields = ('id', 'amount')


class RecipeAddSerializer(serializers.ModelSerializer):
    ingredients = AddIngredientSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    #tags = serializers.PrimaryKeyRelatedField(
    #    queryset=TagInRecipe.objects.all(), many=True)
   # ingredients = AddIngredientSerializer(many=True)
    author = UserSerializer(read_only=True)
    image = HybridImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'ingredients', 'tags', 'image',
            'name', 'text', 'cooking_time')

    def validate(self, data):
        ingredients = data['ingredients']
        ingredients_list = []
        for ingredient in ingredients:
            ingredient_id = ingredient['id']
            if ingredient_id in ingredients_list:
                raise serializers.ValidationError({
                    'ingredients': 'Ingredients shoud be unique)'
                })
            ingredients_list.append(ingredient_id)
            amount = ingredient['amount']
            if int(amount) <= 0:
                raise serializers.ValidationError({
                    'amount': 'Is the quantity value exactly greater than 0?'
                })
        tags = data['tags']
        if not tags:
            raise serializers.ValidationError({
                'tags': 'Tag must be added)'
            })
        tags_list = []
        for tag in tags:
            if tag in tags_list:
                raise serializers.ValidationError({
                    'tags': 'Tags shoud be unique)'
                })
            tags_list.append(tag)
        cooking_time = data['cooking_time']
        if int(cooking_time) <= 0:
            raise serializers.ValidationError({
                'cooking_time': 'Cooking time must not be less than 1 minute'
            })
        return data
    
    def create_bulk(self, recipe, ingredients_data):
        IngredientList.objects.bulk_create([IngredientList(
            ingredient=ingredient['ingredient'],
            recipe=recipe,
            amount=ingredient['amount']
        ) for ingredient in ingredients_data])

   # @staticmethod
  #  def ingredients_create(ingredients, recipe):
       # with transaction.atomic():
  #      for ingredient in ingredients:
   #         IngredientList.objects.create(
    #            recipe=recipe, ingredient=ingredient['name'], #new
     #           amount=ingredient['amount']
      #      )

    #@staticmethod
    #def tags_create(tags, recipe):
      #  with transaction.atomic():
     #   for tag in tags:
      #      recipe_tag = TagInRecipe.objects.create(
       #         recipe=recipe,
        #        tag_id=tag,
         #   )
          #  recipe_tag.save() 

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request')
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(author=request.user, **validated_data)
        recipe.save()
        recipe.tags.set(tags_data)
        self.create_bulk(recipe, ingredients_data)
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
   # def to_representation(self, instance):
   #     request = self.context.get('request')
   #     context = {'request': request}
   #     return RecipeSerializer(instance, context=context).data
    def to_representation(self, instance):
        data = RecipeSerializer(
            instance,
            context={'request': self.context.get('request')}
        ).data
        return data
    #def update(self, instance, validated_data):
    #    if 'tags' in self.validated_data:
    #        tags = validated_data.pop('tags')
    #        self.tags_create(tags, instance)
    #    if 'ingredients' in self.validated_data:
    #        ingredients = validated_data.pop('ingredients')
          #  amount_set = IngredientList.objects.filter(
          #      recipe__id=instance.id
          #  )
           # amount_set.delete()
       #     self.ingredients_create(ingredients, instance)
        #return super().update(instance, validated_data) 


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
