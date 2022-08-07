from django.contrib.auth.models import AbstractUser
from django.db import models

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class User(AbstractUser):
    
    email = models.EmailField(
        max_length=254,
        unique=True,
        blank=False,
        null=False,
        verbose_name='email'
    )
    username = models.CharField(
        max_length=150,
        blank=False,
        null=False,
        verbose_name='username'
    )
    first_name = models.CharField(
        max_length=150,
        blank=False,
        null=False,
        verbose_name='first name'
    )
    last_name = models.CharField(
        max_length=150,
        blank=False,
        null=False,
        verbose_name='last name',
    )
    password = models.CharField(
        max_length=150,
        blank=False,
        null=False,
        verbose_name='password',
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['username']

    def __str__(self):
        return self.get_full_name()
