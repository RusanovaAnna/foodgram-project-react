from colorfield.fields import ColorField
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from users.models import User

MIN = 1


class Tag(models.Model):
    name = models.CharField(
        verbose_name='name',
        max_length=40,
        unique=True,
        null=False,
    )
    color = ColorField(
        unique=True,
        verbose_name='color',
    )
    slug = models.SlugField(
        verbose_name='slug',
        unique=True,
    )

    class Meta:
        ordering = ('-id',)
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='name',
    )
    measurement_unit = models.CharField(
        'measurement_unit',
        max_length=200,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='name_unit_unique'
            )
        ]
        ordering = ('name',)
        verbose_name = 'ingredient'
        verbose_name_plural = 'ingredients'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='author',
        null=True,
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='ingredients',
        through='IngredientList',
    )
    tags = models.ManyToManyField(
        'Tag',
        through='TagInRecipe',
        verbose_name='tags',
    )
    image = models.ImageField(
        upload_to='media/',
        verbose_name='image',
        help_text='Select image to upload)',
    )
    name = models.CharField(
        max_length=200,
        verbose_name='name',
    )
    text = models.TextField(
        verbose_name='recipe description',
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(MIN)],
        verbose_name='cooking time',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'author'],
                name='recipe_unique'
            )
        ]
        verbose_name = 'Recipe'
        verbose_name_plural = 'Recipes'

    def __str__(self):
        return self.name


class TagInRecipe(models.Model):
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name='recipe_tag',
        verbose_name='tag'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        related_name='recipe_tag',
        verbose_name='recipe'
    ) 

    class Meta:
        verbose_name = 'tag in recipe'
        verbose_name_plural = 'tags in recipe'
        constraints = [
            models.UniqueConstraint(
                fields=['tag', 'recipe'],
                name='recipe_tag_unique'
            )
        ] 

    def __str__(self):
        return f'Tag "{self.tag}" recipe "{self.recipe}".' 


class FavoriteRecipe(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='favorite_recipes',
        on_delete=models.CASCADE,
        verbose_name='user',
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='favorite',
        on_delete=models.CASCADE,
        verbose_name='recipe',
    )
    is_favorited = models.BooleanField(
        default=False,
        verbose_name='is favorited',
    )
    is_in_shopping_cart = models.BooleanField(
        default=False,
        verbose_name='is in shopping cart',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'user'],
                name='unique_favorite_recipe',
            )
        ]
        verbose_name = _('Favorites')
        verbose_name_plural = _('Favorites')

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'


class IngredientList(models.Model):
    recipe = models.ForeignKey(
        'Recipe',
        related_name='amount',
        on_delete=models.CASCADE,
        verbose_name='recipe',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='ingredient',
        related_name='amount',
        null=True
    )
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='amount',
        null=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient',
            )
        ]
        verbose_name = 'Ingredient amount'
        verbose_name_plural = 'Ingredient amounts'


class Shop(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='purchases',
        verbose_name='Buyer'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='purchases',
        verbose_name='recipe'
    )

    class Meta:
        verbose_name = 'shop'
        verbose_name_plural = 'shops'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='shop_user_recipe_unique'
            )
        ]

    def __str__(self):
        return f'Recipe "{self.recipe}" in shoplist {self.user}'
