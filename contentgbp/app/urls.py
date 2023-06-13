from django.urls import path
from .views import *
from app import views
urlpatterns = [
    path('', views.home, name='home'),
    # path('register/', views.register, name='register'),
    # path('login/', views.user_login, name='login'),
    # path('logout/', views.user_logout, name='logout'),
    path("post-content-tool/", postContent_tool, name="post-content-tool"),
    path("gmb-description/", gmb_description, name="gmb-description"),
    path("api/upload/", FileUploadAPIView.as_view(), name="file-upload"),
    path("api/gmb-upload/", GenerateGMBDescriptionAPIView.as_view(), name="gmb-upload"),
]
