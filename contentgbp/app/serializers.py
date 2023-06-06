from rest_framework import serializers
from .models import *

class ContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Content
        fields = (
            "id",
            "company_name",
            "character_long",
            "category",
            "keywords",
            "city",
            "tech_name",
            "stars",
            "review_writing_style",
            "content",
            "flag",
        )



class GMBDescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GMBDescription
        fields = ['id', 'keyword', 'location', 'brand_name', 'category', 'description','seo_description']
