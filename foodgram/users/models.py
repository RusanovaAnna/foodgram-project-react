from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.db.models import Q


class CustomUserManager(UserManager):

    def get_by_natural_key(self, username):
        return self.get(
            Q(**{self.model.USERNAME_FIELD: username}),
            Q(**{self.model.EMAIL_FIELD: username}),
        )


class User(AbstractUser):

    email = models.EmailField(
        max_length=254,
        unique=True,
        blank=False,
        null=False,
        verbose_name='email',
    )
    username = models.CharField(
        max_length=150,
        blank=False,
        null=False,
        verbose_name='username',
    )
    first_name = models.CharField(
        max_length=150,
        blank=False,
        null=False,
        verbose_name='first name',
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
    objects = CustomUserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['username']

    def __str__(self):
        return self.get_full_name()


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='follower',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='author',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'user'],
                name='unique_subscribe'
            )
        ]
