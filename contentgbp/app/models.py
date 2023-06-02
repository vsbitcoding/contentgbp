from django.db import models


class YourModel(models.Model):
    company_name = models.CharField(max_length=255)
    character_long = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    keywords = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    tech_name = models.CharField(max_length=255)
    stars = models.IntegerField()
    review_writing_style = models.CharField(max_length=255)
    content = models.TextField(blank=True, null=True)
    flag = models.BooleanField(default=False)

    def __str__(self):
        return self.company_name

class ChatGptKey(models.Model):
    secret_key = models.CharField(max_length=10000)

    def __str__(self):
        return self.secret_key