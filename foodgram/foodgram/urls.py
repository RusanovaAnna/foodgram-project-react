from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('api/auth/', include('djoser.urls.authtoken')),
    path('admin/', admin.site.urls),
    #path('auth/', include('djoser.urls')),
    #path('auth/', include('djoser.urls.jwt')),
    #path("api/users/",include("users.urls"))
]
