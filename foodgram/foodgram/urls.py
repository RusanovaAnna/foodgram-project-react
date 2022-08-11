from django.contrib import admin
#from django.conf import settings
#from django.conf.urls.static import static
from django.urls import path, include
#from django.views.generic import TemplateView



urlpatterns = [
    path('admin/', admin.site.urls),
   # path('', include('recipes.urls', namespace='recipes')),
   # path('auth/', include('users.urls', namespace='users')),
    #path('auth/', include('django.contrib.auth.urls')),
    path('api/', include('api.urls')),
    #path('api/', include('users.urls')),
    #path(
    #    'redoc/',
    #    TemplateView.as_view(template_name='redoc.html'),
    #    name='redoc'
    #),
]