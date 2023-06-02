from django.urls import path
from .views import *

urlpatterns = [
    path("", home, name="home"),
    # path('register/', views.register, name='register'),
    # path('login/', views.login, name='login'),
    # path('logout/', views.logout, name='logout'),
    path("post-content-tool/", postContent_tool, name="post-content-tool"),
    path("api/upload/", FileUploadAPIView.as_view(), name="file-upload"),
]
