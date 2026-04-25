from django.db import models

# Create your models here.


class Defects(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'В работе'),
        ('monitoring', 'Мониторинг'),
        ('closed', 'Закрыт'),
        ('repeat', 'Повтор')
    ]

    title = models.CharField()
    responsible_department = models.CharField(blank=True, null=True)
    responsible_line = models.CharField(blank=True, null=True)
    responsible_station = models.CharField(blank=True, null=True)
    responsible_person = models.CharField(blank=True, null=True)
    countermeasure = models.TextField(blank=True, null=True)
    quality_remark = models.CharField(blank=True, null=True)
    approval_by_quality = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    meeting_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(choices=STATUS_CHOICES, default='in_process')
    #photo = models.ImageField('Фото', upload_to='defects/', blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
