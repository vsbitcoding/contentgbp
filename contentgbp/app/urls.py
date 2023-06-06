from django.urls import path
from .views import *

urlpatterns = [
    path("", home, name="home"),
    # path('register/', views.register, name='register'),
    # path('login/', views.login, name='login'),
    # path('logout/', views.logout, name='logout'),
    path("post-content-tool/", postContent_tool, name="post-content-tool"),
    path("gmb-description/", gmb_description, name="post-content-tool"),
    path("api/upload/", FileUploadAPIView.as_view(), name="file-upload"),
    path("api/gmb-upload/", GenerateGMBDescriptionAPIView.as_view(), name="file-upload"),
    path('content/delete/<int:pk>/', ContentDeleteView.as_view(), name='content-delete'),
    path('content/delete-all/', ContentDeleteAllView.as_view(), name='content-delete-all'),
]
