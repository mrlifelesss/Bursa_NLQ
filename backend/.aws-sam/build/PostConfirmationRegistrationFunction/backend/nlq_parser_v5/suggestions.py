import json, unicodedata, re, sys, pathlib
p = pathlib.Path("scripts/nlq_parser_v5/company_aliases.json")  # adjust path if needed
data = json.loads(p.read_text(encoding="utf-8"))

def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = s.replace("\u00A0", " ").replace("\u202F", " ")  # NBSP → space
    s = s.replace("\u05BE", "-").replace("־", "-")      # maqaf → hyphen
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s

# 1) do we have a key that equals "אל על" (with common variants)?
targets = ["אל על", "אל-על", "אל־על", "אל\u00A0על", "אל\u202Fעל"]
print("Exact key present?", any(norm(k)==norm("אל על") for k in data.keys()))

# 2) show any keys containing אל על
hits = [k for k in data.keys() if "אל" in k]
print("Sample keys with אל:", hits[:20])
