from django.contrib import admin
from .models import Departments, Profile


@admin.register(Departments)
class DefectsAdmin(admin.ModelAdmin):
    list_display = 'department',


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = "pk", "user__username", "user__is_superuser", "department"
    list_display_links = ["user__username"]
    ordering = ["pk", ]
    search_fields = ["user__username", ]


