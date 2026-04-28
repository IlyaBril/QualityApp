from django.contrib import admin
from .models import Defects


@admin.register(Defects)
class DefectsAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'responsible_department',
        'responsible_line',
        'responsible_station',
        'responsible_person',
        'countermeasure',
        'quality_remark',
        'approval_by_quality',
        'created_at',
        'meeting_date',
        ]
