from django.contrib import admin
from django.contrib.admin import ModelAdmin, register

from .forms import CustomUserCreationForm
from .models import Subscription, User


@register(User)
class UserAdmin(ModelAdmin):
    add_form = CustomUserCreationForm
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'password',
    )
    search_fields = ('username', 'email',)
    list_filter = ('username', 'email', 'first_name',)
    empty_value_display = '-'


class SubscriptionAdmin(ModelAdmin):
    list_display = (
        'id',
        'user',
        'author'
    )
    search_fields = ('user__username', 'author__username')


admin.site.register(Subscription, SubscriptionAdmin)
