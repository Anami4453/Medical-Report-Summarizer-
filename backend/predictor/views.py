from rest_framework.decorators import api_view
from rest_framework.response import Response
from transformers import pipeline

# 🔹 Load summarization model (only once)
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

@api_view(["POST"])
def summarize_report(request):
    try:
        text = request.data.get("text", "")
        if not text:
            return Response({"error": "No text provided."}, status=400)

        # 🔹 Generate summary
        summary = summarizer(
            text,
            max_length=150,
            min_length=40,
            do_sample=False
        )[0]["summary_text"]

        return Response({"summary": summary})
    except Exception as e:
        return Response({"error": str(e)}, status=500)
