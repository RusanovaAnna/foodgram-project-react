from django.urls import include, path
from dotenv import load_dotenv
from rest_framework.routers import DefaultRouter

from . import views
from users.views import UserViewSet

load_dotenv()


app_name = 'api'

router = DefaultRouter()

router.register("users", UserViewSet, basename="users")
router.register('tags', views.TagViewSet, basename='tags')
router.register('recipes', views.RecipeViewSet,
                basename='recipes')
router.register('ingredients', views.IngredientsViewSet,
                basename='ingredients')


urlpatterns = [
    path("", include(router.urls)),
    path("", include("djoser.urls")),
    path("auth/", include("djoser.urls.authtoken")),
]
#urlpatterns = [
#    path('', include(router.urls)),
#    path(
#        'auth/token/login/',
#        views.CustomTokenCreateView.as_view(), name='login'
#    ),
#    path('auth/token/logout/', TokenDestroyView.as_view(), name='logout')
#]

