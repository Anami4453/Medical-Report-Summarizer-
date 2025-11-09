from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import MedicalReport
from .serializers import ReportSerializer
from .utils import extract_text_from_pdf, extract_text_from_docx, sanitize_text

class ReportViewSet(viewsets.ModelViewSet):
    """
    Handles uploading, listing, and summarizing medical reports.
    """
    queryset = MedicalReport.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        # Each user can only see their own uploaded reports
        return MedicalReport.objects.filter(user=self.request.user).order_by("-uploaded_at")

    def perform_create(self, serializer):
        """
        When a user uploads a file, extract the text automatically.
        """
        report = serializer.save(user=self.request.user)
        f = report.original_file
        text = ""

        if f:
            fpath = f.path
            name = f.name.lower()

            if name.endswith(".pdf"):
                text = extract_text_from_pdf(fpath)
            elif name.endswith(".docx"):
                text = extract_text_from_docx(fpath)
            else:
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as file:
                        text = file.read()
                except Exception:
                    text = ""

        # sanitize extracted text to remove non-printable/control characters
        report.extracted_text = sanitize_text(text)
        report.save()

    @action(detail=True, methods=["post"])
    def summarize(self, request, pk=None):
        """
        Optional custom endpoint:
        POST /api/reports/<id>/summarize/
        Returns a dummy summary for now.
        """
        try:
            report = self.get_object()
            text = sanitize_text(report.extracted_text or "")
            if not text:
                return Response({"error": "No extracted text found."}, status=status.HTTP_400_BAD_REQUEST)

            # 🔹 Replace this dummy summary with your actual AI summarization logic later
            summary = text[:200] + "..." if len(text) > 200 else text

            report.summary = summary
            report.save()

            return Response({"summary": summary}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
