import django_tables2 as tables
from django.utils.html import format_html
from .models import Defects


class DefectsTable(tables.Table):

    photo_preview = tables.Column(
        verbose_name="Изображение",
        empty_values=(),
        orderable=False,
    )

    actions = tables.Column(
        empty_values=(),
        orderable=False,
    )

    class Meta:
        model = Defects
        attrs = {"class": "table table-striped-columns"}
        fields = [
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
            'actions',
            'photo_preview',
        ]

    def render_photo_preview(self, record):
        print(record.photo.url)
        if record.photo:

            return format_html(f'<img src="{record.photo.url}" style="max-width: 100px; max-height: 100px;" />')
        return format_html('<span class="text-muted">Нет фото</span>')

    def render_actions(self, record):
        return format_html(f'<button class="btn btn-sm btn-primary edit-defect" data-id="{record.id}"')
