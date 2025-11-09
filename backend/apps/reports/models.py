from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

def upload_to(instance, filename):
    return f"reports/{filename}"

class MedicalReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="report_reports")
    original_file = models.FileField(upload_to=upload_to, blank=True, null=True)
    extracted_text = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - Report {self.id}"
