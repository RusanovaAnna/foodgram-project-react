from django.db import transaction
from drf_extra_fields.fields import HybridImageField
from recipes.models import (FavoriteRecipe, Ingredient, IngredientList, Recipe,
                            Shop, Tag, TagInRecipe)
from rest_framework import serializers
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
    

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeShortSerializer(instance.recipe, context=context).data


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
  

    def validate(self, data):
        method = self.context.get('request').method
        author = self.context.get('request').user
        recipe_name = data.get('name')
        ingredients = self.initial_data.get('ingredients')
        tags = self.initial_data.get('tags')
        if method == 'PATCH':
            if ingredients:
                self.ingredients_validate(ingredients)
                data['ingredients'] = ingredients
            if tags:
                self.tag_validate(tags)
                data['tags'] = tags
        if method in ('POST', 'PUT'):
            if (method == 'POST'
                and Recipe.objects.filter(author=author,
                                          name=recipe_name).exists()):
                raise serializers.ValidationError(
                    'You already have this recipe)'
                )
            self.ingredients_validate(ingredients)
            self.tag_validate(tags)

            if method == 'POST':
                data['author'] = author
            data['ingredients'] = ingredients
            data['tags'] = tags
        return data


    def ingredients_validate(self, ingredients):
        ingredients_set = set()
        if not ingredients:
            raise serializers.ValidationError(
                'Ingredient must be added)'
            )
        for ingredient in ingredients:
            amount = ingredient.get('amount')
            ingredient_id = ingredient.get('id')
            if not Ingredient.objects.filter(id=ingredient_id).exists():
                raise serializers.ValidationError(
                    'There is no such ingredient yet('
                )
            if ingredient_id in ingredients_set:
                raise serializers.ValidationError(
                    'Ingredient should not be repeated))'
                )
            try:
                int(amount)
            except ValueError:
                raise serializers.ValidationError(
                    'Ingredient quantity must be a number'
                )
            if int(amount) < 1:
                raise serializers.ValidationError(
                    'Is the quantity value exactly greater than 1?'
                )
            ingredients_set.add(ingredient_id)


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
                recipe_tag = TagInRecipe.objects.create(
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
                    self.get_ingredients(ingredients, recipe)
                if tags:
                    TagInRecipe.objects.filter(recipe=recipe).delete()
                    self.get_tags(tags, recipe)
            else:
                IngredientList.objects.filter(recipe=recipe).delete()
                TagInRecipe.objects.filter(recipe=recipe).delete()
                self.get_ingredients_tags(ingredients, tags, recipe)


    def bool_response(self, request_obj, main_obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return main_obj.objects.filter(user=request.user,
                                       recipe=request_obj.id).exists()


    def get_is_favorited(self, obj):
        return self.bool_response(obj, FavoriteRecipe)


    def get_is_in_shopping_cart(self, obj):
        return self.bool_response(obj, Shop)

