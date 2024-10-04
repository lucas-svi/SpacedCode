# spaced_code/urls.py

from django.contrib import admin
from django.urls import path, include
from core.views import CustomLoginView, CustomLogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', CustomLoginView.as_view(template_name='registration/login.html'), name='login'), 
    path('logout/', CustomLogoutView.as_view(), name='logout'),  
    path('', include('core.urls')), 
]
