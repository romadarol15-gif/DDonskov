from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from tasks_app.views import custom_logout

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('tasks_app.urls')),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', custom_logout, name='logout'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)