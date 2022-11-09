from django.urls import include, path, re_path
#from djoser.views import TokenDestroyView #TokenCreateView
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
   # path('auth/', include('djoser.urls.authtoken')),
    re_path(r'^auth/', include('djoser.urls.authtoken')),
    path('', include('djoser.urls')),
   # path('auth/token/login/', CustomTokenCreateView.as_view(), name='login'),
   # path('token/login/', TokenCreateView.as_view()),
   # path('auth/token/login/', TokenCreateView.as_view(), name='login'),
    path('', include(router_v1.urls)),
   # path('token/logout/', TokenDestroyView.as_view()),
   # path('auth/token/logout/', TokenDestroyView.as_view(), name='logout'),
]
