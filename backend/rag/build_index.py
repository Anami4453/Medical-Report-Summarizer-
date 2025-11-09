from sentence_transformers import SentenceTransformer
import faiss, os, json
import numpy as np
ROOT = os.path.dirname(os.path.dirname(__file__))
MODEL = SentenceTransformer("all-MiniLM-L6-v2")
kb = []  # list of dicts {"id":..., "text":..., "meta":...}
# load your disease knowledge base file - e.g., dataset/disease_kb.jsonl
kbfile = os.path.join(ROOT,"dataset","disease_kb.jsonl")
with open(kbfile,"r",encoding="utf8") as fh:
    for i,line in enumerate(fh):
        rec = json.loads(line.strip())
        kb.append(rec)
texts = [r["text"] for r in kb]
emb = MODEL.encode(texts, show_progress_bar=True)
d = emb.shape[1]
index = faiss.IndexFlatIP(d)
faiss.normalize_L2(emb)
index.add(emb)
faiss.write_index(index, os.path.join(ROOT,"rag_index.faiss"))
with open(os.path.join(ROOT,"rag_kb.json"),"w",encoding="utf8") as out:
    json.dump(kb,out)
print("Built RAG index")
