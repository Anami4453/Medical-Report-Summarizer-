from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import ReportSummary
from .serializers import SummarySerializer
from apps.reports.models import MedicalReport
from django.conf import settings
import openai, os, json

# local model imports (joblib)
try:
    import joblib  # type: ignore[reportMissingImports]
except Exception:
    joblib = None  # type: ignore

MODEL_PATH = os.path.join(settings.BASE_DIR, "diseases_model", "model.pkl")
VECT_PATH = os.path.join(settings.BASE_DIR, "diseases_model", "vectorizer.pkl")
_local_model = None
_vectorizer = None
if joblib is not None and os.path.exists(MODEL_PATH) and os.path.exists(VECT_PATH):
    try:
        _local_model = joblib.load(MODEL_PATH)
        _vectorizer = joblib.load(VECT_PATH)
    except Exception:
        _local_model = None
        _vectorizer = None

# Attempt to locate a finetuned HuggingFace checkpoint under backend/train/checkpoints
HF_FINETUNED_MODEL = None
HF_TOKENIZER = None
HF_DEVICE = None
LATEST_CKPT = None
try:
    CKPT_DIR = os.path.join(settings.BASE_DIR, "train", "checkpoints")
    if os.path.isdir(CKPT_DIR):
        ckpts = [os.path.join(CKPT_DIR, f) for f in os.listdir(CKPT_DIR) if f.endswith('.pt') or f.endswith('.bin')]
        ckpts.sort(key=lambda p: os.path.getmtime(p), reverse=True)
        if ckpts:
            LATEST_CKPT = ckpts[0]
except Exception:
    LATEST_CKPT = None

if LATEST_CKPT:
    try:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        import torch
        HF_DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        HF_BASE = "t5-small"
        HF_TOKENIZER = AutoTokenizer.from_pretrained(HF_BASE)
        HF_MODEL = AutoModelForSeq2SeqLM.from_pretrained(HF_BASE)
        state = torch.load(LATEST_CKPT, map_location=HF_DEVICE)
        HF_MODEL.load_state_dict(state)
        HF_MODEL.to(HF_DEVICE)
        HF_MODEL.eval()
        HF_FINETUNED_MODEL = HF_MODEL
    except Exception:
        HF_FINETUNED_MODEL = None
        HF_TOKENIZER = None

openai.api_key = settings.OPENAI_API_KEY

def llm_summarize(text):
    # Prefer local finetuned HF model if available
    if HF_FINETUNED_MODEL and HF_TOKENIZER:
        try:
            import torch
            inputs = HF_TOKENIZER(text, max_length=512, truncation=True, return_tensors="pt").to(HF_DEVICE)
            summary_ids = HF_FINETUNED_MODEL.generate(inputs.input_ids, attention_mask=inputs.attention_mask, max_length=150, num_beams=4)
            out = HF_TOKENIZER.decode(summary_ids[0], skip_special_tokens=True)
            return out.strip()
        except Exception:
            pass

    # fallback to OpenAI if key present
    if settings.OPENAI_API_KEY:
        res = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role":"system","content":"You are a concise medical summarizer."},
                      {"role":"user","content":f"Summarize the following medical report concisely for a clinician:\n\n{text}"}],
            max_tokens=400,
            temperature=0.0
        )
        return res.choices[0].message["content"].strip()

    # last resort: truncation
    return text[:800] + ("..." if len(text) > 800 else "")

def llm_analyze_symptoms(text):
    if not settings.OPENAI_API_KEY:
        return "No OpenAI key"
    prompt = f"From the clinical text below, extract a list of symptoms (comma separated) and list possible diseases (short list). Text:\n\n{text}\n\nReturn JSON: {{'symptoms': [...], 'possible_diseases': [...]}}"
    res = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}],
        max_tokens=400,
        temperature=0.0
    )
    content = res.choices[0].message["content"].strip()
    # attempt to parse JSON from model response
    try:
        # model might return codeblock; extract first {...}
        import re
        m = re.search(r"\{.*\}", content, re.S)
        js = m.group(0) if m else content
        parsed = json.loads(js)
        return parsed
    except Exception:
        return {"raw": content}

def local_predict(symptom_text):
    if _local_model is None:
        return []
    X = _vectorizer.transform([symptom_text])
    preds = _local_model.predict_proba(X)
    classes = _local_model.classes_
    top_idxs = preds[0].argsort()[::-1][:5]
    return [{"disease": classes[i], "score": float(preds[0][i])} for i in top_idxs]

class SummaryViewSet(viewsets.ModelViewSet):
    queryset = ReportSummary.objects.all()
    serializer_class = SummarySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ReportSummary.objects.filter(report__user=self.request.user).order_by("-created_at")

    def create(self, request, *args, **kwargs):
        report_id = request.data.get("report")
        if not report_id:
            return Response({"detail":"report id required"}, status=status.HTTP_400_BAD_REQUEST)
        report = MedicalReport.objects.get(id=report_id, user=request.user)
        text = report.extracted_text or ""
        summary_text = llm_summarize(text)
        analysis = llm_analyze_symptoms(text)
        # predicted diseases from local model
        pred = []
        if isinstance(analysis, dict):
            symptom_text = ", ".join(analysis.get("symptoms", [])) if analysis.get("symptoms") else text[:500]
        else:
            symptom_text = text[:500]
        if _local_model:
            pred = local_predict(symptom_text)

        summ = ReportSummary.objects.create(report=report, summary_text=summary_text, analysis_text=json.dumps(analysis), predicted_diseases=json.dumps(pred))
        ser = self.get_serializer(summ)
        out = ser.data
        out["analysis_parsed"] = analysis
        out["predicted_diseases_parsed"] = pred
        return Response(out, status=status.HTTP_201_CREATED)
