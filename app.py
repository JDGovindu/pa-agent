import streamlit as st
import anthropic
import chromadb
import json
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import random

st.set_page_config(
    page_title="PA Agent",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
  [data-testid="stAppViewContainer"] { background: #f7f7f5; }
  [data-testid="stSidebar"] { background: #ffffff; }
  .topbar {
    background: white;
    border-bottom: 1px solid #e8e8e4;
    padding: 12px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: -1rem -1rem 1.5rem -1rem;
  }
  .logo { font-size: 15px; font-weight: 600; color: #111; display: flex; align-items: center; gap: 8px; }
  .logo-dot { width: 10px; height: 10px; border-radius: 50%; background: #1D9E75; display: inline-block; }
  .nav-pill {
    display: inline-block; padding: 5px 14px; border-radius: 20px;
    font-size: 12px; font-weight: 500; cursor: pointer; margin-right: 4px;
    border: 1px solid #e8e8e4; background: white; color: #666;
  }
  .nav-pill-active { background: #E1F5EE; color: #085041; border-color: transparent; }
  .stat-card {
    background: white; border: 1px solid #e8e8e4; border-radius: 12px;
    padding: 14px 16px; cursor: pointer; transition: border-color 0.15s;
  }
  .stat-card:hover { border-color: #c0c0bc; }
  .stat-card-active { border-color: #1D9E75 !important; background: #f0fbf7; }
  .stat-num { font-size: 26px; font-weight: 600; margin-bottom: 2px; }
  .stat-label { font-size: 11px; color: #888; }
  .case-card {
    background: white; border: 1px solid #e8e8e4; border-radius: 10px;
    padding: 12px 16px; margin-bottom: 8px; cursor: pointer;
    transition: border-color 0.15s; border-left-width: 4px;
  }
  .case-card:hover { border-color: #c0c0bc; }
  .case-card-blocked { border-left-color: #E24B4A; }
  .case-card-review { border-left-color: #EF9F27; }
  .case-card-ready { border-left-color: #1D9E75; }
  .case-card-submitted { border-left-color: #888; }
  .badge {
    display: inline-block; font-size: 10px; padding: 2px 8px;
    border-radius: 20px; font-weight: 600;
  }
  .badge-blocked { background: #FCEBEB; color: #791F1F; }
  .badge-review { background: #FAEEDA; color: #633806; }
  .badge-ready { background: #E1F5EE; color: #085041; }
  .badge-submitted { background: #F1EFE8; color: #444441; }
  .badge-dismissed { background: #F1EFE8; color: #888; }
  .reason-tag {
    font-size: 11px; padding: 4px 10px; border-radius: 6px;
    margin-top: 6px; display: inline-block; line-height: 1.4;
  }
  .reason-doc { background: #FCEBEB; color: #791F1F; border: 1px solid #F09595; }
  .reason-clin { background: #FAEEDA; color: #633806; border: 1px solid #FAC775; }
  .reason-stale { background: #FAEEDA; color: #633806; border: 1px solid #FAC775; }
  .reason-conflict { background: #EEEDFE; color: #3C3489; border: 1px solid #AFA9EC; }
  .detail-card {
    background: white; border: 1px solid #e8e8e4; border-radius: 10px;
    padding: 14px 16px; margin-bottom: 10px;
  }
  .detail-card-title { font-size: 12px; font-weight: 600; color: #333; margin-bottom: 10px; }
  .signal-tag {
    font-size: 10px; padding: 1px 7px; border-radius: 20px; font-weight: 600;
  }
  .tag-doc { background: #EEEDFE; color: #3C3489; }
  .tag-clin { background: #E6F1FB; color: #0C447C; }
  .tag-ok { background: #E1F5EE; color: #085041; }
  .action-bar {
    background: white; border-top: 1px solid #e8e8e4;
    padding: 14px 16px; border-radius: 0 0 10px 10px;
    margin-top: 0;
  }
  .fetch-bar {
    background: #f0fbf7; border: 1px solid #9FE1CB; border-radius: 8px;
    padding: 7px 14px; font-size: 12px; color: #085041;
    margin-bottom: 14px; display: flex; align-items: center; gap: 8px;
  }
  .history-item {
    font-size: 11px; color: #888; padding: 4px 0;
    border-bottom: 1px solid #f0f0ec;
  }
  .history-item:last-child { border-bottom: none; }
  .block-banner {
    background: #FCEBEB; border: 1px solid #F09595; border-radius: 8px;
    padding: 10px 14px; font-size: 12px; color: #791F1F;
    margin-bottom: 10px; line-height: 1.6;
  }
  .warn-banner {
    background: #FAEEDA; border: 1px solid #FAC775; border-radius: 8px;
    padding: 10px 14px; font-size: 12px; color: #633806;
    margin-bottom: 10px; line-height: 1.6;
  }
  .ready-banner {
    background: #E1F5EE; border: 1px solid #9FE1CB; border-radius: 8px;
    padding: 10px 14px; font-size: 12px; color: #085041;
    margin-bottom: 10px; line-height: 1.6;
  }
  .score-big { font-size: 36px; font-weight: 700; }
  .divider { border: none; border-top: 1px solid #e8e8e4; margin: 12px 0; }
  .step-label {
    font-size: 11px; font-weight: 600; color: #333;
    margin-bottom: 4px; margin-top: 10px;
  }
  .step-label:first-child { margin-top: 0; }
</style>
""", unsafe_allow_html=True)

# ── Secrets ───────────────────────────────────────────────────────────────────
def get_secret(key, fallback=""):
    try:
        return st.secrets[key]
    except Exception:
        return fallback

ANTHROPIC_KEY = get_secret("ANTHROPIC_API_KEY")
GMAIL_USER    = get_secret("GMAIL_USER")
GMAIL_PASS    = get_secret("GMAIL_APP_PASSWORD")

# ── ChromaDB ──────────────────────────────────────────────────────────────────
@st.cache_resource
def get_chroma():
    client = chromadb.PersistentClient(path="./chroma_db")
    col = client.get_or_create_collection(
        name="payer_policies",
        metadata={"hnsw:space": "cosine"}
    )
    return client, col

chroma_client, policy_col = get_chroma()

# ── Test cases ────────────────────────────────────────────────────────────────
TEST_CASES = [
    {
        "id": "TC-01", "name": "Robert M.", "age_gender": "58M",
        "payer": "UnitedHealthcare PPO",
        "diagnosis": "Severe lumbar spinal stenosis (M48.06)",
        "treatment": "Lumbar decompression — laminectomy (CPT 63047)",
        "physician": "Dr. Sarah Mehta, MD — Orthopedic Spine Surgery",
        "facility": "Baylor Scott & White Medical Center, Dallas TX",
        "notes": "Patient presents with 14-month history of progressive bilateral lower extremity pain, numbness, and weakness consistent with neurogenic claudication. MRI L-spine (Jan 2026) confirms severe central canal stenosis at L3-L4 and L4-L5 with nerve root compression. Patient has failed 6 months of conservative management including physical therapy (24 sessions, outcome: no improvement documented by PT). Two epidural steroid injections (Oct 2025, Dec 2025) with documented no sustained relief. Walking tolerance reduced to less than 1 block. Unable to perform ADLs. VAS pain score 8/10 at rest. EMG confirms bilateral L4 radiculopathy. Board-certified orthopedic surgeon recommends surgical intervention.",
        "simulated_docs": {
            "MRI radiology report": {"status": "valid", "detail": "Found · dated 3 months ago · confirms severe stenosis · within UHC 12-month window"},
            "Physical therapy records": {"status": "valid", "detail": "Found · 24 sessions · outcome: documented failure"},
            "ESI procedure notes": {"status": "valid", "detail": "Found · x2 injections · dates and outcomes documented"}
        }
    },
    {
        "id": "TC-02", "name": "Patricia L.", "age_gender": "64F",
        "payer": "UnitedHealthcare PPO",
        "diagnosis": "Lumbar spinal stenosis (M48.06)",
        "treatment": "Lumbar decompression — laminectomy (CPT 63047)",
        "physician": "Dr. Anil Rao, MD — Neurosurgery",
        "facility": "Texas Health Presbyterian Hospital",
        "notes": "Patient presents with 9-month history of lumbar pain with bilateral leg pain. MRI L-spine (Oct 2025) confirms stenosis at L4-L5. Physical therapy completed — 16 sessions, outcome documented as failed. Symptoms ongoing, walking tolerance significantly reduced. Pain described as significant. Board-certified neurosurgeon recommends surgery. No epidural steroid injection documented.",
        "simulated_docs": {
            "MRI radiology report": {"status": "stale", "detail": "Found · but dated 6 months ago · approaching UHC 12-month limit · acceptable but monitor"},
            "Physical therapy records": {"status": "valid", "detail": "Found · 16 sessions · outcome: failure documented"},
            "ESI procedure notes": {"status": "missing", "detail": "Not found in EHR — no ESI record for this patient"}
        }
    },
    {
        "id": "TC-03", "name": "David K.", "age_gender": "71M",
        "payer": "UnitedHealthcare PPO",
        "diagnosis": "Severe lumbar spinal stenosis (M48.06)",
        "treatment": "Lumbar decompression — laminectomy (CPT 63047)",
        "physician": "Dr. James Okafor, MD — Orthopedic Spine Surgery",
        "facility": "Methodist Dallas Medical Center",
        "notes": "Patient presents with 18-month history of progressive neurogenic claudication. MRI L-spine confirms severe central stenosis — imaging performed 14 months ago. Physical therapy 20 sessions — documented failure. Two ESIs with no sustained relief documented. Walking tolerance less than half a block. VAS pain score 9/10. Cannot walk without aid. Board-certified orthopedic surgeon.",
        "simulated_docs": {
            "MRI radiology report": {"status": "stale", "detail": "Found · but dated 14 months ago · outside UHC 12-month window · high denial risk on this basis"},
            "Physical therapy records": {"status": "valid", "detail": "Found · 20 sessions · documented failure"},
            "ESI procedure notes": {"status": "valid", "detail": "Found · x2 · dates and outcomes present"}
        }
    },
    {
        "id": "TC-04", "name": "Angela R.", "age_gender": "45F",
        "payer": "UnitedHealthcare PPO",
        "diagnosis": "Lumbar disc herniation (M51.16)",
        "treatment": "Lumbar laminectomy (CPT 63047)",
        "physician": "Dr. Chen Wei, MD — Spine Surgery",
        "facility": "Parkland Memorial Hospital",
        "notes": "Patient has back pain. Surgery recommended by treating physician. Patient unable to continue daily activities.",
        "simulated_docs": {
            "MRI radiology report": {"status": "missing", "detail": "Not found in EHR — no imaging record for this patient"},
            "Physical therapy records": {"status": "missing", "detail": "Not found in EHR — no PT records"},
            "ESI procedure notes": {"status": "missing", "detail": "Not found in EHR — no ESI record"}
        }
    },
    {
        "id": "TC-05", "name": "Marcus T.", "age_gender": "53M",
        "payer": "UnitedHealthcare PPO",
        "diagnosis": "Lumbar spinal stenosis (M48.06)",
        "treatment": "Lumbar decompression — laminectomy (CPT 63047)",
        "physician": "Dr. Priya Sharma, MD — Neurosurgery",
        "facility": "UT Southwestern Medical Center",
        "notes": "Patient with 10-month lumbar pain history. MRI confirms stenosis at L3-L4 (4 months ago). ESI administered first in treatment sequence, then physical therapy started after. PT completed 12 sessions. Symptoms ongoing. VAS pain score 7/10. Limited ADLs. Board-certified neurosurgeon. ESI preceded PT in treatment timeline.",
        "simulated_docs": {
            "MRI radiology report": {"status": "valid", "detail": "Found · 4 months ago · confirms stenosis · within window"},
            "Physical therapy records": {"status": "valid", "detail": "Found · 12 sessions · but outcome notes say patient improving, not failed"},
            "ESI procedure notes": {"status": "valid", "detail": "Found · but administered before PT — sequence may not satisfy UHC policy"}
        }
    },
    {
        "id": "TC-06", "name": "Susan W.", "age_gender": "67F",
        "payer": "UnitedHealthcare PPO",
        "diagnosis": "Lumbar spinal stenosis (M48.06)",
        "treatment": "Lumbar decompression — laminectomy (CPT 63047)",
        "physician": "Dr. Maria Santos, MD — Orthopedic Surgery",
        "facility": "Baylor University Medical Center",
        "notes": "Patient with 12-month lumbar stenosis history. MRI confirms stenosis (2 months ago). Two ESIs documented with outcome notes. Physical therapy records present. PT notes from therapist say patient improving. Surgeon notes say patient failed PT. Pain score documented as 3/10 in nursing notes, 8/10 in surgeon notes from same week. Symptoms ongoing per surgeon.",
        "simulated_docs": {
            "MRI radiology report": {"status": "valid", "detail": "Found · 2 months ago · confirms stenosis · within window"},
            "Physical therapy records": {"status": "valid", "detail": "Found · but PT outcome says improving while surgeon says failed — conflicting"},
            "ESI procedure notes": {"status": "valid", "detail": "Found · x2 · dates and outcomes documented"}
        }
    }
]

# ── Session state init ────────────────────────────────────────────────────────
if "cases" not in st.session_state:
    st.session_state.cases = {}
if "screen" not in st.session_state:
    st.session_state.screen = "listing"
if "selected_case_id" not in st.session_state:
    st.session_state.selected_case_id = None
if "filter" not in st.session_state:
    st.session_state.filter = "all"
if "last_fetch" not in st.session_state:
    st.session_state.last_fetch = datetime.now() - timedelta(minutes=random.randint(3, 12))
if "api_key_override" not in st.session_state:
    st.session_state.api_key_override = ""

def get_api_key():
    return st.session_state.api_key_override or ANTHROPIC_KEY

# ── Helpers ───────────────────────────────────────────────────────────────────
def chunk_text(text, size=500, overlap=100):
    words = text.split()
    chunks, i = [], 0
    while i < len(words):
        chunks.append(" ".join(words[i:i+size]))
        i += size - overlap
    return chunks

def ingest_policy(text, name):
    chunks = chunk_text(text)
    existing = policy_col.count()
    policy_col.add(
        documents=chunks,
        ids=[f"{name}_{existing+i}" for i in range(len(chunks))],
        metadatas=[{"policy": name} for _ in chunks]
    )
    return len(chunks)

def retrieve_policy(query, n=4):
    if policy_col.count() == 0:
        return []
    results = policy_col.query(query_texts=[query], n_results=min(n, policy_col.count()))
    return [{"text": d, "policy": results["metadatas"][0][i].get("policy","Unknown")}
            for i, d in enumerate(results["documents"][0])]

def state_badge(state):
    mapping = {
        "blocked": "badge-blocked",
        "needs_review": "badge-review",
        "ready_to_submit": "badge-ready",
        "submitted": "badge-submitted",
        "dismissed": "badge-dismissed"
    }
    labels = {
        "blocked": "BLOCKED",
        "needs_review": "NEEDS REVIEW",
        "ready_to_submit": "READY TO SUBMIT",
        "submitted": "SUBMITTED",
        "dismissed": "DISMISSED"
    }
    cls = mapping.get(state, "badge-submitted")
    lbl = labels.get(state, state.upper())
    return f'<span class="badge {cls}">{lbl}</span>'

def score_color(score):
    if score >= 85: return "#1D9E75"
    if score >= 50: return "#EF9F27"
    return "#E24B4A"

def determine_state(score, docs):
    critical_missing = any(
        d["status"] == "missing" for d in docs.values()
    )
    if score < 50 or critical_missing:
        return "blocked"
    if score == 100 and all(d["status"] == "valid" for d in docs.values()):
        return "ready_to_submit"
    return "needs_review"

def format_time(dt):
    return dt.strftime("%b %d, %Y · %I:%M %p")

# ── Agent evaluation ──────────────────────────────────────────────────────────
def run_agent(case, api_key):
    policy_chunks = retrieve_policy(
        f"{case['diagnosis']} {case['treatment']} prior authorization medical necessity"
    )
    policy_context = "\n\n".join(
        [f"[{c['policy']}]\n{c['text']}" for c in policy_chunks]
    ) if policy_chunks else "No policy loaded. Use general UHC medical necessity criteria for lumbar surgery."

    doc_context = "\n".join([
        f"- {name}: {info['status'].upper()} — {info['detail']}"
        for name, info in case["simulated_docs"].items()
    ])

    prompt = f"""You are a senior prior authorization specialist AI. Evaluate this case and return ONLY valid JSON, no markdown.

PATIENT CASE:
- Patient: {case['name']}, {case['age_gender']}
- Payer: {case['payer']}
- Diagnosis: {case['diagnosis']}
- Treatment: {case['treatment']}
- Physician: {case['physician']}
- Clinical notes: {case['notes']}

DOCUMENT AUDIT FROM EHR:
{doc_context}

PAYER POLICY CONTEXT:
{policy_context}

SCORING RULES:
- Score 0-100 reflecting BOTH clinical evidence quality AND document completeness
- If any critical document is MISSING, score must be below 50 regardless of clinical notes
- If all criteria evidenced AND all documents valid, score can reach 100
- Score 50-99 for cases with minor gaps or stale/problematic documents
- Score below 50 for weak clinical evidence OR missing critical documents

Return this exact JSON:
{{
  "confidence_score": <0-100 integer>,
  "state": "blocked" or "needs_review" or "ready_to_submit",
  "block_type": "document_missing" or "weak_clinical" or "both" or null,
  "block_reason_short": "one short phrase for listing page" or null,
  "state_reason": "one sentence explaining the state for the banner",
  "criteria": [
    {{
      "name": "criterion name",
      "status": "met" or "not_met" or "partial",
      "signal_type": "clinical" or "document",
      "detail": "one sentence finding",
      "action": "what coordinator should do if not met" or null
    }}
  ],
  "what_to_do": [
    {{"step": 1, "who": "Physician or Records dept or Coordinator", "action": "specific action to take"}}
  ],
  "icd10_codes": ["code — description"],
  "cpt_codes": ["code — description"],
  "pa_letter": "Full formal PA letter text using \\n for line breaks"
}}"""

    client = anthropic.Anthropic(api_key=api_key)
    resp = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = re.sub(r"```json|```", "", resp.content[0].text).strip()
    result = json.loads(raw)

    # Enforce state consistency with our rules
    result["state"] = determine_state(
        result["confidence_score"],
        case["simulated_docs"]
    )
    return result

def send_email(to, subject, body):
    msg = MIMEMultipart()
    msg["From"] = GMAIL_USER
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(GMAIL_USER, GMAIL_PASS)
        s.send_message(msg)

# ═══════════════════════════════════════════════════════════════════════════════
# SCREENS
# ═══════════════════════════════════════════════════════════════════════════════

def render_topbar():
    col1, col2, col3 = st.columns([2, 3, 2])
    with col1:
        st.markdown(
            '<div class="logo"><span class="logo-dot"></span>PA Agent</div>',
            unsafe_allow_html=True
        )
    with col2:
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Cases", use_container_width=True,
                        type="primary" if st.session_state.screen in ["listing","detail"] else "secondary"):
                st.session_state.screen = "listing"
                st.session_state.selected_case_id = None
                st.rerun()
        with c2:
            if st.button("New case", use_container_width=True,
                        type="primary" if st.session_state.screen == "new_case" else "secondary"):
                st.session_state.screen = "new_case"
                st.rerun()
        with c3:
            if st.button("Policy docs", use_container_width=True,
                        type="primary" if st.session_state.screen == "policy" else "secondary"):
                st.session_state.screen = "policy"
                st.rerun()
    with col3:
        if not get_api_key():
            key = st.text_input("API key", type="password",
                               placeholder="sk-ant-...", label_visibility="collapsed")
            if key:
                st.session_state.api_key_override = key
                st.rerun()
        else:
            st.markdown(
                '<div style="font-size:12px;color:#1D9E75;text-align:right;padding-top:8px">✓ API key loaded</div>',
                unsafe_allow_html=True
            )

# ── Screen 1: Listing ─────────────────────────────────────────────────────────
def screen_listing():
    cases = st.session_state.cases
    fetch_time = format_time(st.session_state.last_fetch)

    st.markdown(
        f'<div class="fetch-bar">↻ &nbsp;Last EHR fetch: {fetch_time} &nbsp;·&nbsp; {len(cases)} cases loaded</div>',
        unsafe_allow_html=True
    )

    blocked   = [c for c in cases.values() if c.get("state") == "blocked"]
    review    = [c for c in cases.values() if c.get("state") == "needs_review"]
    ready     = [c for c in cases.values() if c.get("state") == "ready_to_submit"]
    submitted = [c for c in cases.values() if c.get("state") == "submitted"]
    dismissed = [c for c in cases.values() if c.get("state") == "dismissed"]

    st.markdown("#### Case queue")
    st.markdown(
        '<p style="font-size:12px;color:#888;margin-top:-8px;margin-bottom:16px">Cases evaluated by agent on arrival · sorted by urgency · click to act</p>',
        unsafe_allow_html=True
    )

    c1, c2, c3, c4 = st.columns(4)
    filters = {
        "blocked": (c1, len(blocked), "#E24B4A", "Blocked"),
        "needs_review": (c2, len(review), "#EF9F27", "Needs review"),
        "ready_to_submit": (c3, len(ready), "#1D9E75", "Ready to submit"),
        "submitted": (c4, len(submitted)+len(dismissed), "#888", "Closed"),
    }
    for key, (col, count, color, label) in filters.items():
        with col:
            active = st.session_state.filter == key
            if st.button(
                f"**{count}**\n\n{label}",
                key=f"filter_{key}",
                use_container_width=True,
                type="primary" if active else "secondary"
            ):
                st.session_state.filter = "all" if active else key
                st.rerun()

    st.markdown("<div style='margin-top:16px'></div>", unsafe_allow_html=True)

    active_filter = st.session_state.filter
    def show_group(group, title, card_class):
        if not group:
            return
        if active_filter == "all" or active_filter == group[0].get("state",""):
            st.markdown(
                f'<div style="font-size:10px;font-weight:600;color:#888;text-transform:uppercase;'
                f'letter-spacing:0.05em;margin:12px 0 6px">{title} — {len(group)} cases</div>',
                unsafe_allow_html=True
            )
            for case in group:
                render_case_row(case, card_class)

    show_group(blocked, "Blocked", "case-card-blocked")
    show_group(review, "Needs review", "case-card-review")
    show_group(ready, "Ready to submit", "case-card-ready")
    show_group(submitted + dismissed, "Closed", "case-card-submitted")

    if not cases:
        st.info("No cases loaded yet. Go to **New case** to load cases from the EHR.")

def render_case_row(case, card_class):
    result = case.get("result", {})
    state = case.get("state", "")
    score = result.get("confidence_score", "—")
    score_col = score_color(score) if isinstance(score, int) else "#888"
    badge = state_badge(state)

    block_type = result.get("block_type")
    reason_short = result.get("block_reason_short", "")

    if state == "blocked" and block_type == "document_missing":
        reason_html = f'<div class="reason-tag reason-doc">📄 &nbsp;Document missing — {reason_short}</div>'
    elif state == "blocked" and block_type == "weak_clinical":
        reason_html = f'<div class="reason-tag reason-clin">⚠ &nbsp;Weak clinical evidence — {reason_short}</div>'
    elif state == "blocked" and block_type == "both":
        reason_html = f'<div class="reason-tag reason-doc">📄 &nbsp;Document + clinical gaps — {reason_short}</div>'
    elif state == "needs_review":
        reason_short = result.get("state_reason", "")[:80]
        reason_html = f'<div class="reason-tag reason-stale">↻ &nbsp;{reason_short}</div>'
    else:
        reason_html = ""

    evals = case.get("eval_history", [])
    last_eval = f"Evaluated {format_time(evals[-1]['time'])}" if evals else "Pending evaluation"

    st.markdown(f"""
    <div class="case-card {card_class}">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px">
        <div style="flex:1;font-size:13px;font-weight:600;color:#111">{case['name']} &nbsp;·&nbsp; {case['age_gender']}</div>
        {badge}
        <div style="font-size:15px;font-weight:700;color:{score_col}">{score}</div>
      </div>
      <div style="font-size:11px;color:#888;margin-bottom:4px">{case['diagnosis']} &nbsp;·&nbsp; {case['payer']}</div>
      <div style="font-size:10px;color:#aaa">{last_eval}</div>
      {reason_html}
    </div>
    """, unsafe_allow_html=True)

    if st.button(f"Open case →", key=f"open_{case['id']}", use_container_width=False):
        st.session_state.selected_case_id = case["id"]
        st.session_state.screen = "detail"
        st.rerun()

# ── Screen 2: Case Detail ─────────────────────────────────────────────────────
def screen_detail():
    case_id = st.session_state.selected_case_id
    case = st.session_state.cases.get(case_id)
    if not case:
        st.error("Case not found.")
        return

    result = case.get("result", {})
    state = case.get("state", "")
    score = result.get("confidence_score", 0)

    if st.button("← Back to cases"):
        st.session_state.screen = "listing"
        st.session_state.selected_case_id = None
        st.rerun()

    st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)

    col_head, col_score = st.columns([3, 1])
    with col_head:
        st.markdown(
            f"<div style='font-size:18px;font-weight:700;color:#111'>{case['name']} &nbsp;·&nbsp; {case['age_gender']}</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div style='font-size:12px;color:#888;margin-top:3px'>{case['diagnosis']} &nbsp;·&nbsp; "
            f"{case['treatment']} &nbsp;·&nbsp; {case['payer']}</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div style='font-size:11px;color:#aaa;margin-top:2px'>{case['physician']} &nbsp;·&nbsp; {case['facility']}</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div style='margin-top:8px'>{state_badge(state)}</div>",
            unsafe_allow_html=True
        )
    with col_score:
        color = score_color(score)
        st.markdown(
            f"<div style='text-align:right'>"
            f"<div class='score-big' style='color:{color}'>{score}<span style='font-size:16px;color:#aaa'>/100</span></div>"
            f"<div style='font-size:11px;color:#888'>Confidence score</div>"
            f"<div style='font-size:10px;color:#aaa;margin-top:2px'>Clinical + document</div>"
            f"</div>",
            unsafe_allow_html=True
        )

    st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)

    # State banner
    state_reason = result.get("state_reason", "")
    if state == "blocked":
        st.markdown(f'<div class="block-banner">🚫 &nbsp;<strong>Blocked</strong> — {state_reason}</div>', unsafe_allow_html=True)
    elif state == "needs_review":
        st.markdown(f'<div class="warn-banner">⚠ &nbsp;<strong>Needs review</strong> — {state_reason}</div>', unsafe_allow_html=True)
    elif state == "ready_to_submit":
        st.markdown(f'<div class="ready-banner">✓ &nbsp;<strong>Ready to submit</strong> — {state_reason}</div>', unsafe_allow_html=True)
    elif state == "submitted":
        st.markdown(f'<div class="ready-banner">📤 &nbsp;<strong>Submitted to payer</strong> — Case closed and logged.</div>', unsafe_allow_html=True)
    elif state == "dismissed":
        st.markdown(f'<div class="block-banner" style="background:#F1EFE8;border-color:#ccc;color:#555">✕ &nbsp;<strong>Dismissed</strong> — Case closed without submission.</div>', unsafe_allow_html=True)

    # Main content
    col_left, col_right = st.columns(2)

    with col_left:
        # Criteria check
        st.markdown('<div class="detail-card">', unsafe_allow_html=True)
        st.markdown('<div class="detail-card-title">Criteria check</div>', unsafe_allow_html=True)
        for c in result.get("criteria", []):
            if c["status"] == "met":
                icon, color = "✓", "#1D9E75"
            elif c["status"] == "not_met":
                icon, color = "✗", "#E24B4A"
            else:
                icon, color = "!", "#EF9F27"
            tag_class = "tag-clin" if c["signal_type"] == "clinical" else "tag-doc"
            tag_label = "Clinical" if c["signal_type"] == "clinical" else "Document"
            action_html = (
                f'<div style="font-size:11px;color:#888;margin-top:3px">→ {c["action"]}</div>'
                if c.get("action") and c["status"] != "met" else ""
            )
            st.markdown(f"""
            <div style="display:flex;align-items:flex-start;gap:8px;padding:7px 0;
                        border-bottom:1px solid #f0f0ec;font-size:12px">
              <div style="color:{color};font-weight:700;width:14px;flex-shrink:0;margin-top:1px">{icon}</div>
              <div style="flex:1">
                <div style="font-weight:600;color:#222;margin-bottom:2px">{c['name']}</div>
                <div style="color:#666;line-height:1.5">{c['detail']}</div>
                {action_html}
              </div>
              <span class="signal-tag {tag_class}">{tag_label}</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Codes
        st.markdown('<div class="detail-card">', unsafe_allow_html=True)
        st.markdown('<div class="detail-card-title">ICD-10 &amp; CPT codes</div>', unsafe_allow_html=True)
        for code in result.get("icd10_codes", []):
            st.markdown(f'<span class="signal-tag tag-clin" style="margin:2px;display:inline-block">{code}</span>', unsafe_allow_html=True)
        for code in result.get("cpt_codes", []):
            st.markdown(f'<span class="signal-tag tag-doc" style="margin:2px;display:inline-block">{code}</span>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        # Document audit
        st.markdown('<div class="detail-card">', unsafe_allow_html=True)
        st.markdown('<div class="detail-card-title">Document audit — fetched from EHR</div>', unsafe_allow_html=True)
        for doc_name, doc_info in case["simulated_docs"].items():
            if doc_info["status"] == "valid":
                icon, bg, tc = "✓", "#E1F5EE", "#085041"
            elif doc_info["status"] == "stale":
                icon, bg, tc = "!", "#FAEEDA", "#633806"
            else:
                icon, bg, tc = "✗", "#FCEBEB", "#791F1F"
            st.markdown(f"""
            <div style="display:flex;align-items:flex-start;gap:10px;padding:8px 0;border-bottom:1px solid #f0f0ec">
              <div style="width:24px;height:24px;border-radius:6px;background:{bg};
                          display:flex;align-items:center;justify-content:center;
                          font-size:12px;font-weight:700;color:{tc};flex-shrink:0">{icon}</div>
              <div style="flex:1">
                <div style="font-size:12px;font-weight:600;color:#222;margin-bottom:2px">{doc_name}</div>
                <div style="font-size:11px;color:#888;line-height:1.5">{doc_info['detail']}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # What to do
        if result.get("what_to_do") and state not in ["submitted", "dismissed", "ready_to_submit"]:
            st.markdown('<div class="detail-card">', unsafe_allow_html=True)
            st.markdown('<div class="detail-card-title">What to do next</div>', unsafe_allow_html=True)
            for step in result.get("what_to_do", []):
                st.markdown(f"""
                <div class="step-label">Step {step['step']} — {step['who']}</div>
                <div style="font-size:12px;color:#555;line-height:1.6;margin-bottom:6px">{step['action']}</div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # Re-evaluation history
        evals = case.get("eval_history", [])
        if evals:
            st.markdown('<div class="detail-card">', unsafe_allow_html=True)
            st.markdown('<div class="detail-card-title">Evaluation history</div>', unsafe_allow_html=True)
            for ev in reversed(evals[-5:]):
                label = {"blocked": "🔴 Blocked", "needs_review": "🟡 Needs review",
                         "ready_to_submit": "🟢 Ready"}.get(ev["state"], ev["state"])
                st.markdown(
                    f'<div class="history-item">{label} &nbsp;·&nbsp; score {ev["score"]} &nbsp;·&nbsp; {format_time(ev["time"])}</div>',
                    unsafe_allow_html=True
                )
            st.markdown("</div>", unsafe_allow_html=True)

    # PA Letter preview (for non-blocked, non-dismissed states)
    if state in ["needs_review", "ready_to_submit"] and result.get("pa_letter"):
        with st.expander("Preview PA letter drafted by agent"):
            st.text(result["pa_letter"])

    # Action bar
    st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:10px;font-weight:600;color:#888;text-transform:uppercase;'
        'letter-spacing:0.05em;margin-bottom:8px">Coordinator action</div>',
        unsafe_allow_html=True
    )

    if state in ["submitted", "dismissed"]:
        st.markdown(
            '<div style="font-size:13px;color:#888">This case is closed. No further action needed.</div>',
            unsafe_allow_html=True
        )
        return

    api_key = get_api_key()

    if state == "blocked":
        col_a, col_b = st.columns([1, 1])
        with col_a:
            if st.button("Re-evaluate case", use_container_width=True, type="primary"):
                if not api_key:
                    st.error("No API key found.")
                else:
                    with st.spinner("Agent re-evaluating..."):
                        result = run_agent(case, api_key)
                        case["result"] = result
                        case["state"] = result["state"]
                        case["eval_history"].append({
                            "time": datetime.now(),
                            "score": result["confidence_score"],
                            "state": result["state"]
                        })
                    st.rerun()
        with col_b:
            if st.button("Dismiss case", use_container_width=True):
                case["state"] = "dismissed"
                st.rerun()
        st.markdown(
            '<div style="font-size:11px;color:#888;margin-top:8px">Submit is not available — '
            'resolve the gaps above and re-evaluate. The agent will update the case state automatically.</div>',
            unsafe_allow_html=True
        )

    elif state == "needs_review":
        col_a, col_b, col_c = st.columns([1, 1, 1])
        with col_a:
            if st.button("Re-evaluate case", use_container_width=True, type="secondary"):
                if not api_key:
                    st.error("No API key found.")
                else:
                    with st.spinner("Agent re-evaluating..."):
                        result = run_agent(case, api_key)
                        case["result"] = result
                        case["state"] = result["state"]
                        case["eval_history"].append({
                            "time": datetime.now(),
                            "score": result["confidence_score"],
                            "state": result["state"]
                        })
                    st.rerun()
        with col_b:
            if st.button("Submit — log reason", use_container_width=True, type="primary"):
                st.session_state[f"show_reason_{case_id}"] = True
        with col_c:
            if st.button("Dismiss case", use_container_width=True):
                case["state"] = "dismissed"
                st.rerun()

        if st.session_state.get(f"show_reason_{case_id}"):
            reason = st.text_area(
                "Why are you overriding the review flag? (required)",
                placeholder="e.g. ESI is documented in a separate pain management system not integrated with EHR — confirmed verbally with Dr. Mehta.",
                key=f"reason_input_{case_id}"
            )
            notify = st.text_input("Send PA letter to (email)", placeholder="payer@uhc.com")
            if st.button("Confirm and send", type="primary"):
                if not reason.strip():
                    st.error("Please enter a reason before submitting.")
                else:
                    case["override_reason"] = reason
                    case["state"] = "submitted"
                    case["submitted_at"] = datetime.now()
                    if notify and GMAIL_USER and GMAIL_PASS:
                        try:
                            send_email(notify, f"Prior Authorization — {case['name']}", result.get("pa_letter", ""))
                            st.success(f"PA letter sent to {notify}")
                        except Exception as e:
                            st.warning(f"Could not send email: {e}")
                    del st.session_state[f"show_reason_{case_id}"]
                    st.rerun()

    elif state == "ready_to_submit":
        col_a, col_b = st.columns([2, 1])
        with col_a:
            notify = st.text_input("Send PA letter to (email)", placeholder="payer@uhc.com")
            if st.button("Confirm and submit", use_container_width=True, type="primary"):
                case["state"] = "submitted"
                case["submitted_at"] = datetime.now()
                if notify and GMAIL_USER and GMAIL_PASS:
                    try:
                        send_email(notify, f"Prior Authorization — {case['name']}", result.get("pa_letter", ""))
                        st.success(f"PA letter sent to {notify}")
                    except Exception as e:
                        st.warning(f"Could not send email: {e}")
                st.rerun()
        with col_b:
            st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
            if st.button("Dismiss case", use_container_width=True):
                case["state"] = "dismissed"
                st.rerun()

# ── Screen 3: New Case ────────────────────────────────────────────────────────
def screen_new_case():
    st.markdown("#### New case — EHR intake")
    st.markdown(
        '<p style="font-size:12px;color:#888;margin-top:-8px;margin-bottom:16px">'
        'In production, cases arrive automatically from the EHR. '
        'Select a pre-loaded test case below to simulate EHR intake.</p>',
        unsafe_allow_html=True
    )

    loaded_ids = set(st.session_state.cases.keys())
    unloaded = [tc for tc in TEST_CASES if tc["id"] not in loaded_ids]

    if not unloaded:
        st.success("All test cases have been loaded into the queue.")
        if st.button("Reset all cases"):
            st.session_state.cases = {}
            st.rerun()
        return

    selected_label = st.selectbox(
        "Select case from EHR",
        options=[f"{tc['id']} — {tc['name']}, {tc['age_gender']} — {tc['diagnosis']}" for tc in unloaded]
    )
    selected_tc = unloaded[[f"{tc['id']} — {tc['name']}, {tc['age_gender']} — {tc['diagnosis']}"
                             for tc in unloaded].index(selected_label)]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="detail-card">', unsafe_allow_html=True)
        st.markdown('<div class="detail-card-title">Patient</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="font-size:12px;color:#555;line-height:2">
          <b>Name:</b> {selected_tc['name']}<br>
          <b>Age/Gender:</b> {selected_tc['age_gender']}<br>
          <b>Payer:</b> {selected_tc['payer']}<br>
          <b>Physician:</b> {selected_tc['physician']}
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="detail-card">', unsafe_allow_html=True)
        st.markdown('<div class="detail-card-title">Procedure</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="font-size:12px;color:#555;line-height:2">
          <b>Diagnosis:</b> {selected_tc['diagnosis']}<br>
          <b>Treatment:</b> {selected_tc['treatment']}<br>
          <b>Facility:</b> {selected_tc['facility']}
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="detail-card">', unsafe_allow_html=True)
    st.markdown('<div class="detail-card-title">Clinical notes</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div style="font-size:12px;color:#555;line-height:1.7">{selected_tc["notes"]}</div>',
        unsafe_allow_html=True
    )
    st.markdown("</div>", unsafe_allow_html=True)

    api_key = get_api_key()
    if st.button("Send to agent — evaluate this case", type="primary"):
        if not api_key:
            st.error("No API key found. Enter your Anthropic API key in the top right.")
        else:
            with st.spinner("Agent evaluating case from EHR..."):
                result = run_agent(selected_tc, api_key)
                case_entry = dict(selected_tc)
                case_entry["result"] = result
                case_entry["state"] = result["state"]
                case_entry["eval_history"] = [{
                    "time": datetime.now(),
                    "score": result["confidence_score"],
                    "state": result["state"]
                }]
                st.session_state.cases[selected_tc["id"]] = case_entry
                st.session_state.last_fetch = datetime.now()
            st.success(f"Case evaluated — {result['state'].replace('_',' ').title()} · Score {result['confidence_score']}")
            if st.button("View in queue →"):
                st.session_state.screen = "listing"
                st.rerun()

# ── Screen 4: Policy docs ─────────────────────────────────────────────────────
def screen_policy():
    st.markdown("#### Policy documents")
    st.markdown(
        '<p style="font-size:12px;color:#888;margin-top:-8px;margin-bottom:16px">'
        'Payer policy documents loaded into ChromaDB for RAG retrieval. '
        'The agent queries these on every evaluation.</p>',
        unsafe_allow_html=True
    )

    count = policy_col.count()
    st.markdown(
        f'<div class="fetch-bar">📚 &nbsp;{count} policy chunks loaded in ChromaDB</div>',
        unsafe_allow_html=True
    )

    tab1, tab2 = st.tabs(["Upload PDF", "Paste text"])
    with tab1:
        pdf = st.file_uploader("Upload payer policy PDF", type=["pdf"])
        name = st.text_input("Policy name", placeholder="e.g. UHC_Spine_Surgery_2024")
        if st.button("Ingest PDF") and pdf and name:
            import PyPDF2, io
            reader = PyPDF2.PdfReader(io.BytesIO(pdf.read()))
            text = "".join(p.extract_text() for p in reader.pages)
            n = ingest_policy(text, name)
            st.success(f"✓ {n} chunks added")

    with tab2:
        text = st.text_area("Paste policy text", height=200)
        name2 = st.text_input("Policy name", key="paste_name", placeholder="e.g. UHC_PA_Criteria")
        if st.button("Ingest text") and text and name2:
            n = ingest_policy(text, name2)
            st.success(f"✓ {n} chunks added")

    if st.button("Clear all policies", type="secondary"):
        chroma_client.delete_collection("payer_policies")
        st.success("Cleared.")
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ROUTER
# ═══════════════════════════════════════════════════════════════════════════════
render_topbar()

screen = st.session_state.screen
if screen == "listing":
    screen_listing()
elif screen == "detail":
    screen_detail()
elif screen == "new_case":
    screen_new_case()
elif screen == "policy":
    screen_policy()
