from django.urls import include, path
from dotenv import load_dotenv
from rest_framework import routers

from users.views import UserViewSet
from .views import IngredientsViewSet, RecipeViewSet, TagViewSet

load_dotenv()

app_name = 'api'

router_v1 = routers.DefaultRouter()

router_v1.register('users', UserViewSet, basename='users')
router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register(
    'recipes', RecipeViewSet,
    basename='recipes'
)
router_v1.register(
    'ingredients', IngredientsViewSet,
    basename='ingredients'
)


urlpatterns = [
    path('', include(router_v1.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
