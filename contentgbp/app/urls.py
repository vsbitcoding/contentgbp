from django.urls import path
from .views import *
from app import views
urlpatterns = [
    path('', views.home, name='home'),
    # path('register/', views.register, name='register'),
    # path('login/', views.user_login, name='login'),
    # path('logout/', views.user_logout, name='logout'),
    path("review-content-tool/", postContent_tool, name="review-content-tool"),
    path("gmb-description/", gmb_description, name="gmb-description"),
    path("glosoryterm/", glosory_term, name="glosoryterm"),
    path("glosory-term/", glosory_term2, name="glosory-term"),
    path("api/upload/", FileUploadAPIView.as_view(), name="file-upload"),
    path("api/gmb-upload/", GenerateGMBDescriptionAPIView.as_view(), name="gmb-upload"),
    path("api/glossary-term/", GlossaryTermAPIView.as_view(), name="glossary-term"),
    path("api/glossary-term2/", Glossary2TermAPIView.as_view(), name="glossary-term2"),
]
