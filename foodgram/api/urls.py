from django.urls import include, path
from djoser.views import TokenDestroyView
from dotenv import load_dotenv
from rest_framework import routers

from .views import *
from users.views import UserViewSet

load_dotenv()

app_name = 'api'

router_v1 = routers.DefaultRouter()

router_v1.register('users', UserViewSet, basename='users')
router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('recipes', RecipeViewSet,
                basename='recipes')
router_v1.register('ingredients', IngredientsViewSet,
                basename='ingredients')


urlpatterns = [
    path('', include(router_v1.urls)),
    #path("", include("djoser.urls")),
    path("auth/", include("djoser.urls.authtoken")),
    #path('', include('users.urls')),
    #path('auth/token/login/', views.LoginViewSet, name='login'),
    #path('signup', views.get_confirmation_code, name='get_conf_code'),
#    path('', include(router.urls)),
    path('auth/token/login/', CreateTokenView.as_view(), name='login'),
    path('auth/token/logout/', TokenDestroyView.as_view(), name='logout'),
]

#auth_urlpatterns = [
#    path('login/', views.CustomAuthToken.as_view()),
#    path('logout/', views.DestroyTokenAPIView.as_view()),
#]


#urlpatterns = [
#    path('auth/token/', include(auth_urlpatterns)),
#    path('users/', include(router.urls))
#]

