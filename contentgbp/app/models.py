from django.db import models


class YourModel(models.Model):
    company_name = models.CharField(max_length=255, blank=True, null=True)
    character_long = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(max_length=255, blank=True, null=True)
    keywords = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    tech_name = models.CharField(max_length=255, blank=True, null=True)
    stars = models.IntegerField(blank=True, null=True)
    review_writing_style = models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    flag = models.BooleanField(default=False)

    def __str__(self):
        return self.company_name
