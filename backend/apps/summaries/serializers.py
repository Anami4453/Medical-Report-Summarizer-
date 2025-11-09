from rest_framework import serializers
from .models import ReportSummary

class SummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportSummary
        fields = "__all__"
        read_only_fields = ("created_at",)
