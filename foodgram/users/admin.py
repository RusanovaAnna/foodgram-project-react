from django.contrib import admin
from django.contrib.admin import ModelAdmin, register

from .models import Subscription, User


class UserAdmin(admin.ModelAdmin):
    list_display = ('pk',
                    'username',
                    'email',
                    'first_name',
                    'last_name',
                    'is_active',
                    'last_login',
                    )
    list_editable = ('is_active',)
    search_fields = ('username', 'email')
    empty_value_display = '-'


class SubscriptionAdmin(ModelAdmin):
    list_display = (
        'id',
        'user',
        'author'
    )
    search_fields = ('user__username', 'author__username')


admin.site.register(User, UserAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
