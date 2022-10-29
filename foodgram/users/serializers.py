from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers

from recipes.models import Recipe
from .models import Subscription, User

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):

    is_subscribed = serializers.SerializerMethodField(
        read_only=True
    )
    password = serializers.CharField(write_only=True)

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

    def get_is_subscribed(self, obj):
        user_id = self.context.get('request').user.id
        return Subscription.objects.filter(
            author=obj.id, user=user_id).exists()


class UserRegistrationSerializer(UserCreateSerializer):
    
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'password')


class MeSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('username', 'email',
                  'first_name', 'last_name',)


class RecipeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(
        min_length=8,
        max_length=128,
        write_only=True,
    )
    current_password = serializers.CharField(write_only=True)


class SubscriptionSerializer(serializers.ModelSerializer):
    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source='author.recipes.count')
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count'
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return Subscription.objects.filter(
            author=obj.author, user=user).exists()

    def get_recipes(self, obj):
        limit = self.context.get('request').GET.get('recipes_limit')
        recipe_obj = obj.author.recipes.all()
        if limit:
            recipe_obj = recipe_obj[:int(limit)]
        serializer = RecipeShortSerializer(
            recipe_obj, many=True
        )
        return serializer.data
