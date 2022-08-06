from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from rest_framework.validators import UniqueValidator
from rest_framework.serializers import (ModelSerializer, SerializerMethodField)
from users.models import User
from recipes.models import Ingredient, Recipe, Tag


class GetTokenSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, max_length=100)
    confirmation_code = serializers.CharField(required=True, max_length=100)

    def validate(self, data):
        username = data.get('username')
        user = get_object_or_404(User, username=username)
        confirmation_code = username = data.get('confirmation_code')

        if not default_token_generator.check_token(user, confirmation_code):
            raise serializers.ValidationError('error code')
        return data

    class Meta:
        fields = ('username', 'confirmation_code')
        model = User


class GetConfirmationCode(serializers.ModelSerializer):
    username = serializers.CharField(
        validators=[
            UniqueValidator(queryset=User.objects.all())
        ]
    )
    email = serializers.EmailField(
        validators=[
            UniqueValidator(queryset=User.objects.all())
        ]
    )

    def validate_username(self, value):
        if value == 'me':
            raise serializers.ValidationError('Choose a different name')
        return value

    class Meta:
        fields = ('username', 'email')
        model = User


User = get_user_model()

class UserSerializer(ModelSerializer):

    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'password',
        )
        extra_kwargs = {'password': {'write_only': True}}
        read_only_fields = 'is_subscribed',

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous or (user == obj):
            return False
        return user.subscribe.filter(id=obj.id).exists()

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password'],
        )
        user.save()
        return user


class TagSerializer(ModelSerializer):
    
    class Meta:
        model = Tag
        fields = '__all__'
        read_only_fields = '__all__',

class RecipeSerializer(ModelSerializer):
    #tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = SerializerMethodField()
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = '__all__'
        read_only_fields = (
            'is_favorite',
            'is_shopping_cart',
        )

class IngredientSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'
        read_only_fields = '__all__',


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email',
                  'first_name', 'last_name')