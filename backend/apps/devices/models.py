from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class MedicalReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="device_reports")

    original_file = models.FileField(upload_to="reports/")  # simple path only
    extracted_text = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.original_file.name}"
