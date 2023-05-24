from django.urls import path
from . import views
from .views import *
urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('postContent-tool/', views.postContent_tool, name='postContent-tool'),
    path('api/upload/', FileUploadAPIView.as_view(), name='file-upload'),

]
