from django.db import models
from apps.reports.models import MedicalReport
from django.conf import settings

class ReportSummary(models.Model):
    report = models.ForeignKey(MedicalReport, on_delete=models.CASCADE, related_name="summaries")
    summary_text = models.TextField()
    analysis_text = models.TextField(blank=True)
    predicted_diseases = models.TextField(blank=True)  # CSV / JSON style
    created_at = models.DateTimeField(auto_now_add=True)
