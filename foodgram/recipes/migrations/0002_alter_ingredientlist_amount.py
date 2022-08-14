# Generated by Django 4.0.6 on 2022-08-13 19:07

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingredientlist',
            name='amount',
            field=models.PositiveSmallIntegerField(null=True, validators=[django.core.validators.MinValueValidator(1)], verbose_name='amount'),
        ),
    ]