from rest_framework import serializers
from .models import MedicalReport

class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalReport
        fields = "__all__"
        read_only_fields = ("user","extracted_text","uploaded_at")
