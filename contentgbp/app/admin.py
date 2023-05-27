from .models import *
from django.contrib import admin

# Register your models here.


class ChatGPTAdmin(admin.ModelAdmin):
    list_display = ("secret_key",)
    search_fields = ("secret_key",)

    def has_add_permission(self, request):
        if ChatGptKey.objects.count() == 1:
            return False
        return True

    def render_change_form(
        self, request, context, add=False, change=False, form_url="", obj=None
    ):
        context.update(
            {
                "show_save_and_continue": False,
                "show_save_and_add_another": False,
                "show_delete": False,
            }
        )
        return super().render_change_form(request, context, add, change, form_url, obj)


admin.site.register(ChatGptKey, ChatGPTAdmin)
