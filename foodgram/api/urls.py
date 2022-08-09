from django.urls import include, path
from dotenv import load_dotenv
from rest_framework.routers import DefaultRouter

from . import views
#from users.views import UserViewSet

load_dotenv()


app_name = 'api'

router = DefaultRouter()

#router.register('users', UserViewSet, basename='users')
router.register('tags', views.TagViewSet, basename='tags')
router.register('recipes', views.RecipeViewSet,
                basename='recipes')
router.register('ingredients', views.IngredientsViewSet,
                basename='ingredients')


urlpatterns = [
    path('', include(router.urls)),
    #path("", include("djoser.urls")),
    #path("auth/", include("djoser.urls.authtoken")),
    #path('auth/token/login/', views.LoginViewSet, name='login'),
    #path('signup', views.get_confirmation_code, name='get_conf_code'),
]
#urlpatterns = [
#    path('', include(router.urls)),
#    path(
#        'auth/token/login/',
#        views.CustomTokenCreateView.as_view(), name='login'
#    ),
#    path('auth/token/logout/', TokenDestroyView.as_view(), name='logout')
#]

#auth_urlpatterns = [
#    path('login/', views.CustomAuthToken.as_view()),
#    path('logout/', views.DestroyTokenAPIView.as_view()),
#]


#urlpatterns = [
#    path('auth/token/', include(auth_urlpatterns)),
#    path('users/', include(router.urls))
#]

