import os

from django.urls import include, path
from djoser.views import TokenDestroyView
from dotenv import load_dotenv
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions, routers

from . import views

load_dotenv()


app_name = 'api'

router = routers.DefaultRouter()

router.register('tags', views.TagViewSet, basename='tags')
router.register('recipes', views.RecipeViewSet,
                basename='recipes')
router.register('ingredients', views.IngredientsViewSet,
                basename='ingredients')
router.register('users', views.CustomUserViewSet, basename='users')


#urlpatterns = [
#    path('', include(router.urls)),
#    path(
#        'auth/token/login/',
#        views.CustomTokenCreateView.as_view(), name='login'
#    ),
#    path('auth/token/logout/', TokenDestroyView.as_view(), name='logout')
#]

