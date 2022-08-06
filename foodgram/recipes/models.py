from django.core.validators import MinValueValidator
from django.db import models

#from .validators import year_validator

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from users.models import User

MIN = 1


class Tag(models.Model):
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name='name',
    )
    color = models.CharField(
        max_length=32,
        default='#E26C2D',
        unique=True,
        verbose_name='color',
    )
    slug = models.SlugField(
        max_length=255,
        editable=False,
        verbose_name='slug',
        unique=True,
    )

    class Meta:
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')
        ordering = ['id']

    def __str__(self):
        return self.name


class UnitOfMeasurement(models.Model):
    class Metrics(models.TextChoices):
        mass = _('mass'), _('mass')
        volume = _('volume'), _('volume')
        quantity = _('quantity'), _('quantity')
        percent = _('percent'), _('percent')
        miscellaneous = _('miscellaneous'), _('miscellaneous')

    name = models.CharField(
        max_length=255,
        verbose_name='name',
        unique=True,
    )
    metric = models.CharField(
        max_length=255,
        choices=Metrics.choices,
        verbose_name='metric',
        unique=True,
    )

    class Meta:
        verbose_name = _('unit of measurement')
        verbose_name_plural = _('unit of measurement')
        ordering = ['metric', 'name']

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='name')
    measurement_unit = models.CharField(
        UnitOfMeasurement,
        max_length=200,
        verbose_name='unit of measurement')

    class Meta:
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
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='author',
        unique=True,
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        related_name='recipes',
        through='IngredientAmount',
        verbose_name='ingredients',
    )
    tags = models.ManyToManyField(
        'Tag',
        related_name='recipes',
        verbose_name='tags',
    )
    image = models.ImageField(
        upload_to='recipes/',
        verbose_name='image',
        help_text='Select image to upload)', 
    )
    name = models.CharField(
        max_length=200,
        verbose_name='name',
        unique=True,
    )
    text = models.TextField(
        verbose_name='recipe description',
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(MIN)],
        verbose_name='cooking time',
    )
    #date = models.DateTimeField(
    #    auto_now_add=True,
    #    verbose_name='date',
    #    validators=[year_validator],
    #)

    class Meta:
        verbose_name = 'Recipe'
        verbose_name_plural = 'Recipes'
        ordering = ['date']

    def __str__(self):
        return self.name

    def list_tags(self):
        return self.tags.values_list('name', flat=True)


class FavouriteRecipe(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='favourite_recipes',
        on_delete=models.CASCADE,
        verbose_name='user',
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='in_favourites',
        on_delete=models.CASCADE,
        verbose_name='recipe',
    )
    is_favorited = models.BooleanField(
        default=False,
        verbose_name='is favorited'
    )
    is_in_shopping_cart = models.BooleanField(
        default=False,
        verbose_name='is in shopping cart'
    )
    #added_to_favorites = models.DateTimeField(
    #    auto_now_add=True,
    #    verbose_name='date - added to favorites'
    #)
    #added_to_shopping_cart = models.DateTimeField(
    #    auto_now_add=True,
    #    verbose_name='date - added to shopping cart'
    #)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite_recipe',
            )
        ]
        verbose_name = _('Favorites')
        verbose_name_plural = _('Favorites')
        #ordering = ['-added_to_favorites', '-added_to_shopping_cart']

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'


class IngredientList(models.Model):
    recipe = models.ForeignKey(
        'Recipe',
        related_name='ingredient_list',
        on_delete=models.CASCADE,
        verbose_name=_('recipe')
    )
    ingredient = models.ForeignKey(
        'ingredients.Ingredient',
        related_name='ingredient_list',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('ingredient')
    )
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name=_('ingredient amount')
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient',
            )
        ]
        verbose_name = _('Ingredient amount')
        verbose_name_plural = _('Ingredient amounts')
        ordering = ['id']

    def __str__(self):
        return f'{self.recipe.name} - {self.ingredient.name}'
