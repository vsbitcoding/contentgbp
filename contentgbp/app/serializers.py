from rest_framework import serializers
from .models import Content


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
