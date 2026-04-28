from django.contrib.auth.models import User
from django.db import models


class Departments(models.Model):
    department = models.CharField()

    def __str__(self):
        return self.department


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.ForeignKey(Departments, null=True, on_delete=models.SET_NULL)

