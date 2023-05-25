from rest_framework import serializers
from .models import YourModel

class YourModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = YourModel
        fields = ('id','company_name', 'character_long', 'category', 'keywords', 'city', 'tech_name', 'stars', 'review_writing_style', 'content', 'flag')
