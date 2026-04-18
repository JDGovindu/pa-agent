import streamlit as st
from datetime import datetime, timedelta
import random
import time

st.set_page_config(page_title="PA Agent", page_icon="🏥", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
  [data-testid="stAppViewContainer"] { background:#f7f7f5; }
  .fetch-bar { background:#f0fbf7;border:1px solid #9FE1CB;border-radius:8px;padding:7px 14px;font-size:12px;color:#085041;margin-bottom:14px; }
  .badge { display:inline-block;font-size:10px;padding:2px 9px;border-radius:20px;font-weight:600; }
  .badge-blocked { background:#FCEBEB;color:#791F1F; }
  .badge-needs_review { background:#FAEEDA;color:#633806; }
  .badge-ready_to_submit { background:#E1F5EE;color:#085041; }
  .badge-submitted { background:#F1EFE8;color:#444; }
  .badge-dismissed { background:#F1EFE8;color:#888; }
  .case-card { background:white;border:1px solid #e8e8e4;border-radius:10px;padding:13px 16px;margin-bottom:7px;border-left-width:4px; }
  .case-card-blocked { border-left-color:#E24B4A; }
  .case-card-needs_review { border-left-color:#EF9F27; }
  .case-card-ready_to_submit { border-left-color:#1D9E75; }
  .case-card-submitted,.case-card-dismissed { border-left-color:#ddd; }
  .reason-tag { font-size:11px;padding:3px 9px;border-radius:6px;margin-top:6px;display:inline-block;line-height:1.5; }
  .rt-doc { background:#FCEBEB;color:#791F1F;border:1px solid #F09595; }
  .rt-clin { background:#FAEEDA;color:#633806;border:1px solid #FAC775; }
  .rt-review { background:#FAEEDA;color:#633806;border:1px solid #FAC775; }
  .detail-card { background:white;border:1px solid #e8e8e4;border-radius:10px;padding:14px 16px;margin-bottom:10px; }
  .dct { font-size:10px;font-weight:600;color:#aaa;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:10px; }
  .sig-tag { font-size:10px;padding:1px 7px;border-radius:20px;font-weight:600; }
  .st-doc { background:#EEEDFE;color:#3C3489; }
  .st-clin { background:#E6F1FB;color:#0C447C; }
  .block-banner { background:#FCEBEB;border:1px solid #F09595;border-radius:8px;padding:11px 14px;font-size:12px;color:#791F1F;margin-bottom:0;line-height:1.6; }
  .warn-banner { background:#FAEEDA;border:1px solid #FAC775;border-radius:8px;padding:11px 14px;font-size:12px;color:#633806;margin-bottom:0;line-height:1.6; }
  .ready-banner { background:#E1F5EE;border:1px solid #9FE1CB;border-radius:8px;padding:11px 14px;font-size:12px;color:#085041;margin-bottom:0;line-height:1.6; }
  .sub-banner { background:#F1EFE8;border:1px solid #ccc;border-radius:8px;padding:11px 14px;font-size:12px;color:#444;margin-bottom:0;line-height:1.6; }
  .action-zone { background:white;border:1px solid #e8e8e4;border-radius:10px;padding:14px 16px;margin-bottom:12px; }
  .hist-item { font-size:11px;color:#888;padding:5px 0;border-bottom:1px solid #f5f5f3; }
  .hist-item:last-child { border-bottom:none; }
</style>
""", unsafe_allow_html=True)

# ── Preset results ─────────────────────────────────────────────────────────────
PRESETS = {
"TC-01": [
  {"confidence_score":100,"state":"ready_to_submit","block_type":None,"block_reason_short":None,
   "state_reason":"All criteria fully evidenced and all documents valid. Ready for one-click submission.",
   "criteria":[
     {"name":"MRI imaging","status":"met","signal_type":"document","detail":"MRI confirms severe stenosis at L3-L4, dated 3 months ago, within UHC 12-month window.","action":None},
     {"name":"Physical therapy","status":"met","signal_type":"document","detail":"24 sessions completed, outcome documented as failed.","action":None},
     {"name":"Epidural steroid injection","status":"met","signal_type":"document","detail":"Two ESIs documented with dates and no sustained relief.","action":None},
     {"name":"Symptom duration","status":"met","signal_type":"clinical","detail":"14 months of progressive symptoms documented.","action":None},
     {"name":"Functional impairment","status":"met","signal_type":"clinical","detail":"VAS 8/10, walking under 1 block, unable to perform ADLs.","action":None},
     {"name":"Physician qualification","status":"met","signal_type":"clinical","detail":"Board-certified orthopedic surgeon.","action":None},
   ],
   "docs":{"MRI radiology report":{"status":"valid","detail":"Found · 3 months ago · confirms severe stenosis · within UHC 12-month window"},"Physical therapy records":{"status":"valid","detail":"Found · 24 sessions · outcome: failure documented"},"ESI procedure notes":{"status":"valid","detail":"Found · x2 · dates and outcomes documented"}},
   "what_to_do":[],"icd10_codes":["M48.06 — Lumbar spinal stenosis","M54.4 — Lumbago with sciatica"],"cpt_codes":["CPT 63047 — Laminectomy, lumbar"],
   "pa_letter":"Date: April 19, 2026\n\nTo: UnitedHealthcare PPO — Utilization Management\nFrom: Dr. Sarah Mehta, MD\nRe: Prior Authorization — Robert M., 58M\n\nDear Utilization Management Team,\n\nI am requesting prior authorization for lumbar decompression surgery (CPT 63047) for Robert M., 58-year-old male.\n\nAll UHC medical necessity criteria are satisfied. MRI confirms severe stenosis at L3-L4. Patient has completed 24 sessions of PT with documented failure and two ESIs with no sustained relief. Symptoms present 14 months. VAS 8/10. Unable to perform ADLs.\n\nDocuments enclosed: MRI report, PT records, ESI procedure notes.\n\nSincerely,\nDr. Sarah Mehta, MD\nBaylor Scott & White Medical Center"}
],
"TC-02": [
  {"confidence_score":28,"state":"blocked","block_type":"document_missing","block_reason_short":"ESI procedure note not found in EHR",
   "state_reason":"Critical document missing — no ESI procedure note found. UHC requires at least one documented failed ESI before approving lumbar decompression.",
   "criteria":[
     {"name":"MRI imaging","status":"met","signal_type":"document","detail":"MRI confirms stenosis at L4-L5, dated 6 months ago.","action":None},
     {"name":"Physical therapy","status":"met","signal_type":"document","detail":"16 sessions completed, outcome documented as failed.","action":None},
     {"name":"Epidural steroid injection","status":"not_met","signal_type":"document","detail":"No ESI procedure note found in EHR.","action":"Contact records department — retrieve ESI note or confirm treatment at another facility."},
     {"name":"Symptom duration","status":"met","signal_type":"clinical","detail":"9 months of symptoms documented.","action":None},
     {"name":"Functional impairment","status":"partial","signal_type":"clinical","detail":"Pain described as significant — no numeric VAS score.","action":"Ask physician to add numeric VAS pain score to notes."},
     {"name":"Physician qualification","status":"met","signal_type":"clinical","detail":"Board-certified neurosurgeon.","action":None},
   ],
   "docs":{"MRI radiology report":{"status":"valid","detail":"Found · 6 months ago · within window"},"Physical therapy records":{"status":"valid","detail":"Found · 16 sessions · failure documented"},"ESI procedure notes":{"status":"missing","detail":"Not found in EHR — no ESI record for this patient"}},
   "what_to_do":[{"step":1,"who":"Records department","action":"Search for ESI note — may be in external pain management system. Retrieve and upload to EHR."},{"step":2,"who":"Physician","action":"Add numeric VAS pain score to clinical notes."},{"step":3,"who":"Coordinator","action":"Once updated in EHR, click Re-evaluate case."}],
   "icd10_codes":["M48.06 — Lumbar spinal stenosis"],"cpt_codes":["CPT 63047 — Laminectomy, lumbar"],"pa_letter":""},
  {"confidence_score":64,"state":"needs_review","block_type":None,"block_reason_short":None,
   "state_reason":"ESI document now found. Minor gap remains — no numeric pain score. Coordinator can submit now or re-evaluate after physician updates notes.",
   "criteria":[
     {"name":"MRI imaging","status":"met","signal_type":"document","detail":"MRI confirms stenosis, 6 months ago.","action":None},
     {"name":"Physical therapy","status":"met","signal_type":"document","detail":"16 sessions, failure documented.","action":None},
     {"name":"Epidural steroid injection","status":"met","signal_type":"document","detail":"ESI note now found — injection documented with no sustained relief.","action":None},
     {"name":"Symptom duration","status":"met","signal_type":"clinical","detail":"9 months documented.","action":None},
     {"name":"Functional impairment","status":"partial","signal_type":"clinical","detail":"Still no numeric VAS score — minor gap.","action":"Ask physician to add VAS score before resubmitting."},
     {"name":"Physician qualification","status":"met","signal_type":"clinical","detail":"Board-certified neurosurgeon.","action":None},
   ],
   "docs":{"MRI radiology report":{"status":"valid","detail":"Found · 6 months ago · within window"},"Physical therapy records":{"status":"valid","detail":"Found · 16 sessions · failure documented"},"ESI procedure notes":{"status":"valid","detail":"Found · 1 injection · outcome documented"}},
   "what_to_do":[{"step":1,"who":"Physician","action":"Add numeric VAS pain score to notes to strengthen the submission."},{"step":2,"who":"Coordinator","action":"Re-evaluate to reach Ready to submit, or submit now with reason if timeline is urgent."}],
   "icd10_codes":["M48.06 — Lumbar spinal stenosis","M54.4 — Lumbago with sciatica"],"cpt_codes":["CPT 63047 — Laminectomy, lumbar"],
   "pa_letter":"Date: April 19, 2026\n\nTo: UnitedHealthcare PPO\nFrom: Dr. Anil Rao, MD\nRe: Prior Authorization — Patricia L., 64F\n\nRequesting authorization for CPT 63047. Patient has 9-month stenosis history. PT failed (16 sessions). ESI administered with no sustained relief. Surgical intervention is medically necessary.\n\nSincerely,\nDr. Anil Rao, MD — Texas Health Presbyterian Hospital"},
  {"confidence_score":100,"state":"ready_to_submit","block_type":None,"block_reason_short":None,
   "state_reason":"All criteria fully evidenced and all documents valid. Ready for one-click submission.",
   "criteria":[
     {"name":"MRI imaging","status":"met","signal_type":"document","detail":"MRI confirms stenosis, within window.","action":None},
     {"name":"Physical therapy","status":"met","signal_type":"document","detail":"16 sessions, failure documented.","action":None},
     {"name":"Epidural steroid injection","status":"met","signal_type":"document","detail":"ESI note found, outcome documented.","action":None},
     {"name":"Symptom duration","status":"met","signal_type":"clinical","detail":"9 months documented.","action":None},
     {"name":"Functional impairment","status":"met","signal_type":"clinical","detail":"VAS 7/10 now documented by physician.","action":None},
     {"name":"Physician qualification","status":"met","signal_type":"clinical","detail":"Board-certified neurosurgeon.","action":None},
   ],
   "docs":{"MRI radiology report":{"status":"valid","detail":"Found · within window"},"Physical therapy records":{"status":"valid","detail":"Found · failure documented"},"ESI procedure notes":{"status":"valid","detail":"Found · outcome documented"}},
   "what_to_do":[],"icd10_codes":["M48.06 — Lumbar spinal stenosis"],"cpt_codes":["CPT 63047 — Laminectomy, lumbar"],
   "pa_letter":"Date: April 19, 2026\n\nTo: UnitedHealthcare PPO\nFrom: Dr. Anil Rao, MD\nRe: Prior Authorization — Patricia L., 64F\n\nAll UHC criteria met. Requesting authorization for CPT 63047. Documents enclosed.\n\nSincerely, Dr. Anil Rao, MD"}
],
"TC-03": [
  {"confidence_score":58,"state":"needs_review","block_type":None,"block_reason_short":None,
   "state_reason":"MRI exists but dated 14 months ago — outside UHC 12-month window. Clinical evidence is otherwise strong. Coordinator decides: order new MRI or submit with current.",
   "criteria":[
     {"name":"MRI imaging","status":"partial","signal_type":"document","detail":"MRI confirms severe stenosis but dated 14 months ago — outside UHC 12-month window.","action":"Order updated MRI to eliminate denial risk, or submit with current and log reason."},
     {"name":"Physical therapy","status":"met","signal_type":"document","detail":"20 sessions, failure documented.","action":None},
     {"name":"Epidural steroid injection","status":"met","signal_type":"document","detail":"Two ESIs with no sustained relief.","action":None},
     {"name":"Symptom duration","status":"met","signal_type":"clinical","detail":"18 months of progressive symptoms.","action":None},
     {"name":"Functional impairment","status":"met","signal_type":"clinical","detail":"VAS 9/10, cannot walk without aid.","action":None},
     {"name":"Physician qualification","status":"met","signal_type":"clinical","detail":"Board-certified orthopedic surgeon.","action":None},
   ],
   "docs":{"MRI radiology report":{"status":"stale","detail":"Found · but dated 14 months ago · outside UHC 12-month window · high denial risk"},"Physical therapy records":{"status":"valid","detail":"Found · 20 sessions · failure documented"},"ESI procedure notes":{"status":"valid","detail":"Found · x2 · outcomes documented"}},
   "what_to_do":[{"step":1,"who":"Coordinator","action":"Decide: order a new MRI to eliminate denial risk, or submit now accepting the technical risk."},{"step":2,"who":"Physician","action":"If ordering new MRI — request urgently given symptom severity. Re-evaluate once uploaded to EHR."}],
   "icd10_codes":["M48.06 — Lumbar spinal stenosis"],"cpt_codes":["CPT 63047 — Laminectomy, lumbar"],
   "pa_letter":"Date: April 19, 2026\n\nTo: UnitedHealthcare PPO\nFrom: Dr. James Okafor, MD\nRe: Prior Authorization — David K., 71M\n\nRequesting authorization for CPT 63047. Severe stenosis, 18-month history. PT and ESI both failed. VAS 9/10. Surgical intervention urgently needed.\n\nSincerely,\nDr. James Okafor, MD — Methodist Dallas Medical Center"},
  {"confidence_score":100,"state":"ready_to_submit","block_type":None,"block_reason_short":None,
   "state_reason":"Updated MRI on file and within UHC window. All criteria met.",
   "criteria":[
     {"name":"MRI imaging","status":"met","signal_type":"document","detail":"Updated MRI now on file — dated 2 weeks ago, confirms severe stenosis, within UHC window.","action":None},
     {"name":"Physical therapy","status":"met","signal_type":"document","detail":"20 sessions, failure documented.","action":None},
     {"name":"Epidural steroid injection","status":"met","signal_type":"document","detail":"Two ESIs, no sustained relief.","action":None},
     {"name":"Symptom duration","status":"met","signal_type":"clinical","detail":"18 months.","action":None},
     {"name":"Functional impairment","status":"met","signal_type":"clinical","detail":"VAS 9/10.","action":None},
     {"name":"Physician qualification","status":"met","signal_type":"clinical","detail":"Board-certified orthopedic surgeon.","action":None},
   ],
   "docs":{"MRI radiology report":{"status":"valid","detail":"Updated MRI · 2 weeks ago · within window"},"Physical therapy records":{"status":"valid","detail":"Found · failure documented"},"ESI procedure notes":{"status":"valid","detail":"Found · x2 · documented"}},
   "what_to_do":[],"icd10_codes":["M48.06 — Lumbar spinal stenosis"],"cpt_codes":["CPT 63047 — Laminectomy, lumbar"],
   "pa_letter":"Date: April 19, 2026\n\nTo: UnitedHealthcare PPO\nFrom: Dr. James Okafor, MD\nRe: Prior Authorization — David K., 71M\n\nAll criteria met. Updated MRI on file. Requesting authorization for CPT 63047.\n\nSincerely, Dr. James Okafor, MD"}
],
"TC-04": [
  {"confidence_score":18,"state":"blocked","block_type":"document_missing","block_reason_short":"MRI, PT records, and ESI note not found in EHR",
   "state_reason":"Multiple critical documents missing from EHR and clinical notes are too sparse to establish medical necessity.",
   "criteria":[
     {"name":"MRI imaging","status":"not_met","signal_type":"document","detail":"No MRI report in EHR.","action":"Confirm MRI was performed and retrieve report from radiology."},
     {"name":"Physical therapy","status":"not_met","signal_type":"document","detail":"No PT records in EHR.","action":"Retrieve PT records or confirm treatment at another facility."},
     {"name":"Epidural steroid injection","status":"not_met","signal_type":"document","detail":"No ESI record in EHR.","action":"Confirm ESI was administered and retrieve procedure note."},
     {"name":"Symptom duration","status":"not_met","signal_type":"clinical","detail":"Notes only say 'back pain' — no duration documented.","action":"Physician must document symptom onset, duration, and progression."},
     {"name":"Functional impairment","status":"not_met","signal_type":"clinical","detail":"No VAS score or specific ADL limitations documented.","action":"Physician must add VAS score, walking tolerance, and ADL limitations."},
     {"name":"Physician qualification","status":"met","signal_type":"clinical","detail":"Treating physician identified.","action":None},
   ],
   "docs":{"MRI radiology report":{"status":"missing","detail":"Not found in EHR"},"Physical therapy records":{"status":"missing","detail":"Not found in EHR"},"ESI procedure notes":{"status":"missing","detail":"Not found in EHR"}},
   "what_to_do":[{"step":1,"who":"Records department","action":"Retrieve MRI report, PT records, and ESI note — likely in external systems."},{"step":2,"who":"Physician","action":"Strengthen clinical notes — add symptom duration, VAS score, walking tolerance, ADL limitations."},{"step":3,"who":"Coordinator","action":"Once all in EHR, click Re-evaluate case."}],
   "icd10_codes":["M51.16 — Lumbar disc herniation"],"cpt_codes":["CPT 63047 — Laminectomy, lumbar"],"pa_letter":""},
  {"confidence_score":61,"state":"needs_review","block_type":None,"block_reason_short":None,
   "state_reason":"Documents now retrieved and notes strengthened. Minor gap in symptom duration documentation. Coordinator can review and decide.",
   "criteria":[
     {"name":"MRI imaging","status":"met","signal_type":"document","detail":"MRI retrieved — confirms disc herniation at L4-L5, 5 months ago.","action":None},
     {"name":"Physical therapy","status":"met","signal_type":"document","detail":"PT records retrieved — 14 sessions, failure documented.","action":None},
     {"name":"Epidural steroid injection","status":"met","signal_type":"document","detail":"ESI note retrieved — one injection, no sustained relief.","action":None},
     {"name":"Symptom duration","status":"partial","signal_type":"clinical","detail":"Physician updated notes — 8 months. Borderline but meets UHC minimum.","action":None},
     {"name":"Functional impairment","status":"met","signal_type":"clinical","detail":"VAS 7/10, walking limited to 2 blocks.","action":None},
     {"name":"Physician qualification","status":"met","signal_type":"clinical","detail":"Board-certified spine surgeon.","action":None},
   ],
   "docs":{"MRI radiology report":{"status":"valid","detail":"Retrieved · 5 months ago · within window"},"Physical therapy records":{"status":"valid","detail":"Retrieved · 14 sessions · failure documented"},"ESI procedure notes":{"status":"valid","detail":"Retrieved · 1 injection · no sustained relief"}},
   "what_to_do":[{"step":1,"who":"Coordinator","action":"Review case — all documents now complete. Re-evaluate to reach Ready to submit, or submit now with reason."}],
   "icd10_codes":["M51.16 — Lumbar disc herniation","M54.4 — Lumbago with sciatica"],"cpt_codes":["CPT 63047 — Laminectomy, lumbar"],
   "pa_letter":"Date: April 19, 2026\n\nTo: UnitedHealthcare PPO\nFrom: Dr. Chen Wei, MD\nRe: Prior Authorization — Angela R., 45F\n\nRequesting authorization for CPT 63047. Patient has 8-month disc herniation history. PT failed, ESI failed. VAS 7/10. Surgical intervention is medically necessary.\n\nSincerely, Dr. Chen Wei, MD — Parkland Memorial Hospital"},
  {"confidence_score":100,"state":"ready_to_submit","block_type":None,"block_reason_short":None,
   "state_reason":"All criteria met and all documents valid. Ready for submission.",
   "criteria":[
     {"name":"MRI imaging","status":"met","signal_type":"document","detail":"MRI confirms disc herniation, within window.","action":None},
     {"name":"Physical therapy","status":"met","signal_type":"document","detail":"14 sessions, failure documented.","action":None},
     {"name":"Epidural steroid injection","status":"met","signal_type":"document","detail":"One injection, no sustained relief.","action":None},
     {"name":"Symptom duration","status":"met","signal_type":"clinical","detail":"8 months — meets UHC threshold.","action":None},
     {"name":"Functional impairment","status":"met","signal_type":"clinical","detail":"VAS 7/10, walking limited to 2 blocks.","action":None},
     {"name":"Physician qualification","status":"met","signal_type":"clinical","detail":"Board-certified spine surgeon.","action":None},
   ],
   "docs":{"MRI radiology report":{"status":"valid","detail":"Retrieved · within window"},"Physical therapy records":{"status":"valid","detail":"Retrieved · failure documented"},"ESI procedure notes":{"status":"valid","detail":"Retrieved · outcome documented"}},
   "what_to_do":[],"icd10_codes":["M51.16 — Lumbar disc herniation"],"cpt_codes":["CPT 63047 — Laminectomy, lumbar"],
   "pa_letter":"Date: April 19, 2026\n\nTo: UnitedHealthcare PPO\nFrom: Dr. Chen Wei, MD\nRe: Prior Authorization — Angela R., 45F\n\nAll criteria met. Requesting authorization for CPT 63047. Documents enclosed.\n\nSincerely, Dr. Chen Wei, MD"}
],
"TC-05": [
  {"confidence_score":22,"state":"blocked","block_type":"weak_clinical","block_reason_short":"PT outcome says improving, ESI sequence incorrect",
   "state_reason":"Clinical evidence too weak — PT notes say improving not failed, and ESI was administered before PT which does not satisfy UHC sequencing policy.",
   "criteria":[
     {"name":"MRI imaging","status":"met","signal_type":"document","detail":"MRI confirms stenosis at L3-L4, 4 months ago.","action":None},
     {"name":"Physical therapy","status":"not_met","signal_type":"clinical","detail":"PT records present but outcome says 'patient improving' — UHC requires documented failure.","action":"Physician must amend PT outcome to document treatment failure, not improvement."},
     {"name":"ESI sequence","status":"not_met","signal_type":"clinical","detail":"ESI administered before PT was completed — UHC requires PT failure first.","action":"Physician to document clinical justification for non-standard treatment sequence."},
     {"name":"Symptom duration","status":"met","signal_type":"clinical","detail":"10 months documented.","action":None},
     {"name":"Functional impairment","status":"met","signal_type":"clinical","detail":"VAS 7/10, limited ADLs.","action":None},
     {"name":"Physician qualification","status":"met","signal_type":"clinical","detail":"Board-certified neurosurgeon.","action":None},
   ],
   "docs":{"MRI radiology report":{"status":"valid","detail":"Found · 4 months ago · within window"},"Physical therapy records":{"status":"valid","detail":"Found · but outcome says improving, not failed"},"ESI procedure notes":{"status":"valid","detail":"Found · but administered before PT — sequence concern"}},
   "what_to_do":[{"step":1,"who":"Physician","action":"Amend PT outcome notes to document treatment failure — current notes contradict surgical recommendation."},{"step":2,"who":"Physician","action":"Add clinical justification for ESI being administered before PT completion."},{"step":3,"who":"Coordinator","action":"Once physician updates notes in EHR, click Re-evaluate case."}],
   "icd10_codes":["M48.06 — Lumbar spinal stenosis"],"cpt_codes":["CPT 63047 — Laminectomy, lumbar"],"pa_letter":""},
  {"confidence_score":72,"state":"needs_review","block_type":None,"block_reason_short":None,
   "state_reason":"Physician has updated PT outcome and added ESI justification. Minor scoring gap remains but case is submittable. Coordinator can proceed.",
   "criteria":[
     {"name":"MRI imaging","status":"met","signal_type":"document","detail":"MRI confirms stenosis, within window.","action":None},
     {"name":"Physical therapy","status":"met","signal_type":"clinical","detail":"PT outcome now documents treatment failure — physician amended notes.","action":None},
     {"name":"ESI sequence","status":"partial","signal_type":"clinical","detail":"Clinical justification documented. Payer may still question — be prepared for appeal.","action":None},
     {"name":"Symptom duration","status":"met","signal_type":"clinical","detail":"10 months.","action":None},
     {"name":"Functional impairment","status":"met","signal_type":"clinical","detail":"VAS 7/10.","action":None},
     {"name":"Physician qualification","status":"met","signal_type":"clinical","detail":"Board-certified neurosurgeon.","action":None},
   ],
   "docs":{"MRI radiology report":{"status":"valid","detail":"Found · within window"},"Physical therapy records":{"status":"valid","detail":"Updated · outcome now documents failure"},"ESI procedure notes":{"status":"valid","detail":"Found · clinical justification for sequence added"}},
   "what_to_do":[{"step":1,"who":"Coordinator","action":"Re-evaluate to reach Ready to submit, or submit now with reason noting ESI sequence justification is documented."}],
   "icd10_codes":["M48.06 — Lumbar spinal stenosis"],"cpt_codes":["CPT 63047 — Laminectomy, lumbar"],
   "pa_letter":"Date: April 19, 2026\n\nTo: UnitedHealthcare PPO\nFrom: Dr. Priya Sharma, MD\nRe: Prior Authorization — Marcus T., 53M\n\nRequesting authorization for CPT 63047. PT failure documented. ESI sequence clinical justification enclosed. 10-month history. VAS 7/10.\n\nSincerely, Dr. Priya Sharma, MD — UT Southwestern Medical Center"},
  {"confidence_score":100,"state":"ready_to_submit","block_type":None,"block_reason_short":None,
   "state_reason":"All criteria met. ESI justification accepted. Ready for submission.",
   "criteria":[
     {"name":"MRI imaging","status":"met","signal_type":"document","detail":"MRI confirms stenosis, within window.","action":None},
     {"name":"Physical therapy","status":"met","signal_type":"clinical","detail":"PT failure documented.","action":None},
     {"name":"ESI sequence","status":"met","signal_type":"clinical","detail":"Clinical justification accepted.","action":None},
     {"name":"Symptom duration","status":"met","signal_type":"clinical","detail":"10 months.","action":None},
     {"name":"Functional impairment","status":"met","signal_type":"clinical","detail":"VAS 7/10.","action":None},
     {"name":"Physician qualification","status":"met","signal_type":"clinical","detail":"Board-certified neurosurgeon.","action":None},
   ],
   "docs":{"MRI radiology report":{"status":"valid","detail":"Found · within window"},"Physical therapy records":{"status":"valid","detail":"Updated · failure documented"},"ESI procedure notes":{"status":"valid","detail":"Justified · sequence accepted"}},
   "what_to_do":[],"icd10_codes":["M48.06 — Lumbar spinal stenosis"],"cpt_codes":["CPT 63047 — Laminectomy, lumbar"],
   "pa_letter":"Date: April 19, 2026\n\nTo: UnitedHealthcare PPO\nFrom: Dr. Priya Sharma, MD\nRe: Prior Authorization — Marcus T., 53M\n\nAll criteria met. Requesting authorization for CPT 63047.\n\nSincerely, Dr. Priya Sharma, MD"}
],
"TC-06": [
  {"confidence_score":52,"state":"needs_review","block_type":None,"block_reason_short":None,
   "state_reason":"Conflicting documentation — PT notes say improving while surgeon says failed. Pain score 3/10 in nursing notes vs 8/10 in surgeon notes same week. Must resolve before submission.",
   "criteria":[
     {"name":"MRI imaging","status":"met","signal_type":"document","detail":"MRI confirms stenosis, 2 months ago.","action":None},
     {"name":"Physical therapy","status":"partial","signal_type":"clinical","detail":"PT records present but therapist notes say improving while surgeon says failed — conflicting.","action":"Surgeon letter clarifying PT failure is recommended."},
     {"name":"Epidural steroid injection","status":"met","signal_type":"document","detail":"Two ESIs documented.","action":None},
     {"name":"Symptom duration","status":"met","signal_type":"clinical","detail":"12 months documented.","action":None},
     {"name":"Functional impairment","status":"partial","signal_type":"clinical","detail":"Pain score 3/10 in nursing notes vs 8/10 in surgeon notes same week — conflicting.","action":"Surgeon to document definitive VAS score and resolve discrepancy."},
     {"name":"Physician qualification","status":"met","signal_type":"clinical","detail":"Board-certified orthopedic surgeon.","action":None},
   ],
   "docs":{"MRI radiology report":{"status":"valid","detail":"Found · 2 months ago · within window"},"Physical therapy records":{"status":"valid","detail":"Found · but PT outcome conflicts with surgeon assessment"},"ESI procedure notes":{"status":"valid","detail":"Found · x2 · outcomes documented"}},
   "what_to_do":[{"step":1,"who":"Physician","action":"Add surgeon letter clarifying PT was unsuccessful despite therapist progress note."},{"step":2,"who":"Physician","action":"Document definitive VAS pain score — resolve the 3/10 vs 8/10 discrepancy."},{"step":3,"who":"Coordinator","action":"Once notes are aligned in EHR, re-evaluate case."}],
   "icd10_codes":["M48.06 — Lumbar spinal stenosis","M54.4 — Lumbago with sciatica"],"cpt_codes":["CPT 63047 — Laminectomy, lumbar"],
   "pa_letter":"Date: April 19, 2026\n\nTo: UnitedHealthcare PPO\nFrom: Dr. Maria Santos, MD\nRe: Prior Authorization — Susan W., 67F\n\nRequesting authorization for CPT 63047. 12-month stenosis history. PT and two ESIs failed. MRI confirmed.\n\nSincerely, Dr. Maria Santos, MD — Baylor University Medical Center"},
  {"confidence_score":100,"state":"ready_to_submit","block_type":None,"block_reason_short":None,
   "state_reason":"Documentation conflicts resolved. All criteria met and all documents valid.",
   "criteria":[
     {"name":"MRI imaging","status":"met","signal_type":"document","detail":"MRI confirms stenosis, 2 months ago.","action":None},
     {"name":"Physical therapy","status":"met","signal_type":"clinical","detail":"Surgeon letter added clarifying PT failure — conflict resolved.","action":None},
     {"name":"Epidural steroid injection","status":"met","signal_type":"document","detail":"Two ESIs documented.","action":None},
     {"name":"Symptom duration","status":"met","signal_type":"clinical","detail":"12 months.","action":None},
     {"name":"Functional impairment","status":"met","signal_type":"clinical","detail":"Definitive VAS 8/10 documented — discrepancy resolved.","action":None},
     {"name":"Physician qualification","status":"met","signal_type":"clinical","detail":"Board-certified orthopedic surgeon.","action":None},
   ],
   "docs":{"MRI radiology report":{"status":"valid","detail":"Found · within window"},"Physical therapy records":{"status":"valid","detail":"Surgeon letter added · conflict resolved"},"ESI procedure notes":{"status":"valid","detail":"Found · x2 · documented"}},
   "what_to_do":[],"icd10_codes":["M48.06 — Lumbar spinal stenosis"],"cpt_codes":["CPT 63047 — Laminectomy, lumbar"],
   "pa_letter":"Date: April 19, 2026\n\nTo: UnitedHealthcare PPO\nFrom: Dr. Maria Santos, MD\nRe: Prior Authorization — Susan W., 67F\n\nConflicts resolved. All criteria met. Requesting authorization for CPT 63047.\n\nSincerely, Dr. Maria Santos, MD"}
]
}

TEST_CASES = [
  {"id":"TC-01","name":"Robert M.","age_gender":"58M","payer":"UnitedHealthcare PPO","diagnosis":"Severe lumbar spinal stenosis (M48.06)","treatment":"Lumbar decompression — laminectomy (CPT 63047)","physician":"Dr. Sarah Mehta, MD — Orthopedic Spine Surgery","facility":"Baylor Scott & White Medical Center"},
  {"id":"TC-02","name":"Patricia L.","age_gender":"64F","payer":"UnitedHealthcare PPO","diagnosis":"Lumbar spinal stenosis (M48.06)","treatment":"Lumbar decompression — laminectomy (CPT 63047)","physician":"Dr. Anil Rao, MD — Neurosurgery","facility":"Texas Health Presbyterian Hospital"},
  {"id":"TC-03","name":"David K.","age_gender":"71M","payer":"UnitedHealthcare PPO","diagnosis":"Severe lumbar spinal stenosis (M48.06)","treatment":"Lumbar decompression — laminectomy (CPT 63047)","physician":"Dr. James Okafor, MD — Orthopedic Spine Surgery","facility":"Methodist Dallas Medical Center"},
  {"id":"TC-04","name":"Angela R.","age_gender":"45F","payer":"UnitedHealthcare PPO","diagnosis":"Lumbar disc herniation (M51.16)","treatment":"Lumbar laminectomy (CPT 63047)","physician":"Dr. Chen Wei, MD — Spine Surgery","facility":"Parkland Memorial Hospital"},
  {"id":"TC-05","name":"Marcus T.","age_gender":"53M","payer":"UnitedHealthcare PPO","diagnosis":"Lumbar spinal stenosis (M48.06)","treatment":"Lumbar decompression — laminectomy (CPT 63047)","physician":"Dr. Priya Sharma, MD — Neurosurgery","facility":"UT Southwestern Medical Center"},
  {"id":"TC-06","name":"Susan W.","age_gender":"67F","payer":"UnitedHealthcare PPO","diagnosis":"Lumbar spinal stenosis (M48.06)","treatment":"Lumbar decompression — laminectomy (CPT 63047)","physician":"Dr. Maria Santos, MD — Orthopedic Surgery","facility":"Baylor University Medical Center"},
]

# ── Session state ──────────────────────────────────────────────────────────────
for k,v in [("cases",{}),("screen","listing"),("selected_case_id",None),("filter","all"),
            ("last_fetch", datetime.now()-timedelta(minutes=random.randint(4,14)))]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Helpers ────────────────────────────────────────────────────────────────────
def fmt(dt): return dt.strftime("%b %d, %Y · %I:%M %p")
def slabel(s): return {"blocked":"BLOCKED","needs_review":"NEEDS REVIEW","ready_to_submit":"READY TO SUBMIT","submitted":"SUBMITTED","dismissed":"DISMISSED"}.get(s,s.upper())
def scol(n): return "#1D9E75" if n>=85 else ("#EF9F27" if n>=50 else "#E24B4A")

def load_case(tc):
    stages = PRESETS.get(tc["id"],[])
    if not stages: return
    r = stages[0]
    e = dict(tc)
    e.update({"result":r,"state":r["state"],"stage":0,"eval_history":[{"time":datetime.now(),"score":r["confidence_score"],"state":r["state"]}]})
    st.session_state.cases[tc["id"]] = e
    st.session_state.last_fetch = datetime.now()

def next_result(case_id):
    stages = PRESETS.get(case_id,[])
    c = st.session_state.cases.get(case_id,{})
    ns = min(c.get("stage",0)+1, len(stages)-1)
    return stages[ns], ns

def open_case(cid):
    st.session_state.selected_case_id = cid
    st.session_state.screen = "detail"
    st.rerun()

# ── Nav ────────────────────────────────────────────────────────────────────────
def nav():
    c1,c2,c3 = st.columns([2,5,2])
    with c1:
        st.markdown('''<div style="font-size:15px;font-weight:700;color:#111;padding-top:8px">
          <span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:#1D9E75;margin-right:7px;margin-bottom:1px"></span>PA Agent
        </div>''',unsafe_allow_html=True)
    with c2:
        n1,n2,n3 = st.columns(3)
        for col,(label,scr) in zip([n1,n2,n3],[("Cases","listing"),("New case","new_case"),("Policy docs","policy")]):
            with col:
                cur = st.session_state.screen in (["listing","detail"] if scr=="listing" else [scr])
                if st.button(label,use_container_width=True,type="primary" if cur else "secondary",key=f"nav_{scr}"):
                    st.session_state.screen = scr
                    if scr != "detail": st.session_state.selected_case_id = None
                    st.rerun()
    with c3:
        st.markdown('<div style="font-size:11px;color:#1D9E75;text-align:right;padding-top:10px">Demo mode · No API needed</div>',unsafe_allow_html=True)

# ── Listing ────────────────────────────────────────────────────────────────────
def listing():
    cases = st.session_state.cases
    st.markdown(f'<div class="fetch-bar">↻ &nbsp;Last EHR fetch: {fmt(st.session_state.last_fetch)} &nbsp;·&nbsp; {len(cases)} cases in queue</div>',unsafe_allow_html=True)
    bl=[c for c in cases.values() if c.get("state")=="blocked"]
    rv=[c for c in cases.values() if c.get("state")=="needs_review"]
    rd=[c for c in cases.values() if c.get("state")=="ready_to_submit"]
    sb=[c for c in cases.values() if c.get("state") in ["submitted","dismissed"]]
    st.markdown('<p style="font-size:13px;font-weight:600;color:#111;margin-bottom:4px">Case queue</p>',unsafe_allow_html=True)
    st.markdown('<p style="font-size:11px;color:#888;margin-bottom:14px">Evaluated by agent on arrival · sorted by urgency · click any case to act</p>',unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    for col,key,count,label in [(c1,"blocked",len(bl),"Blocked"),(c2,"needs_review",len(rv),"Needs review"),(c3,"ready_to_submit",len(rd),"Ready to submit"),(c4,"closed",len(sb),"Closed")]:
        with col:
            active = st.session_state.filter==key
            if st.button(f"{count}  \n{label}",key=f"f_{key}",use_container_width=True,type="primary" if active else "secondary"):
                st.session_state.filter = "all" if active else key
                st.rerun()
    st.markdown("<div style='margin-top:16px'></div>",unsafe_allow_html=True)
    f = st.session_state.filter
    def grp(group,title,skey):
        if not group: return
        if f not in ["all",skey,"closed"]: return
        if f=="closed" and skey not in ["submitted","dismissed"]: return
        st.markdown(f'<div style="font-size:10px;font-weight:600;color:#aaa;text-transform:uppercase;letter-spacing:0.05em;margin:10px 0 6px">{title} — {len(group)}</div>',unsafe_allow_html=True)
        for c in group: case_row(c)
    grp(bl,"Blocked","blocked"); grp(rv,"Needs review","needs_review"); grp(rd,"Ready to submit","ready_to_submit")
    if f in ["all","closed"] and sb:
        st.markdown('<div style="font-size:10px;font-weight:600;color:#aaa;text-transform:uppercase;letter-spacing:0.05em;margin:10px 0 6px">Closed</div>',unsafe_allow_html=True)
        for c in sb: case_row(c)
    if not cases:
        st.info("No cases loaded. Go to **New case** to load cases from the EHR.")

def case_row(case):
    r = case.get("result",{}); state = case.get("state","")
    score = r.get("confidence_score","—"); sc = scol(score) if isinstance(score,int) else "#888"
    evals = case.get("eval_history",[]); last = f"Last evaluated {fmt(evals[-1]['time'])}" if evals else ""
    bt = r.get("block_type",""); rs = r.get("block_reason_short",""); sr = r.get("state_reason","")
    if state=="blocked" and bt=="document_missing": rh=f'<div class="reason-tag rt-doc">📄 Document missing — {rs}</div>'
    elif state=="blocked" and bt=="weak_clinical": rh=f'<div class="reason-tag rt-clin">⚠ Weak clinical evidence — {rs}</div>'
    elif state=="blocked": rh=f'<div class="reason-tag rt-doc">📄 Document + clinical gaps — {rs}</div>'
    elif state=="needs_review": short=sr[:85]+("..." if len(sr)>85 else ""); rh=f'<div class="reason-tag rt-review">↻ {short}</div>'
    else: rh=""
    st.markdown(f"""<div class="case-card case-card-{state}">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px">
        <div style="flex:1;font-size:13px;font-weight:600;color:#111">{case['name']} &nbsp;·&nbsp; {case['age_gender']}</div>
        <span class="badge badge-{state}">{slabel(state)}</span>
        <div style="font-size:17px;font-weight:700;color:{sc};min-width:32px;text-align:right">{score}</div>
      </div>
      <div style="font-size:11px;color:#888;margin-bottom:3px">{case['diagnosis'][:55]}{"..." if len(case['diagnosis'])>55 else ""} &nbsp;·&nbsp; {case['payer']}</div>
      <div style="font-size:10px;color:#bbb;margin-bottom:2px">{last}</div>
      {rh}
    </div>""",unsafe_allow_html=True)
    if st.button(f"View case →",key=f"o_{case['id']}",use_container_width=False):
        open_case(case["id"])

# ── Detail ─────────────────────────────────────────────────────────────────────
def detail():
    cid = st.session_state.selected_case_id
    case = st.session_state.cases.get(cid)
    if not case: st.error("Case not found."); return
    r = case.get("result",{}); state = case.get("state",""); score = r.get("confidence_score",0)

    # Back link
    if st.button("← Back to cases"):
        st.session_state.screen="listing"; st.session_state.selected_case_id=None; st.rerun()
    st.markdown("<div style='margin-top:8px'></div>",unsafe_allow_html=True)

    # Header row
    ch,cs = st.columns([3,1])
    with ch:
        st.markdown(f"""<div style="margin-bottom:2px">
          <span style="font-size:18px;font-weight:700;color:#111">{case['name']} &nbsp;·&nbsp; {case['age_gender']}</span>
          &nbsp;&nbsp;<span class="badge badge-{state}">{slabel(state)}</span>
        </div>
        <div style="font-size:12px;color:#888;margin-bottom:2px">{case['diagnosis']} &nbsp;·&nbsp; {case['treatment']}</div>
        <div style="font-size:11px;color:#bbb">{case['physician']} &nbsp;·&nbsp; {case['payer']}</div>""",unsafe_allow_html=True)
    with cs:
        c=scol(score)
        st.markdown(f'''<div style="text-align:right;padding-top:4px">
          <div style="font-size:36px;font-weight:700;color:{c};line-height:1.1">{score}<span style="font-size:14px;color:#ccc;font-weight:400">/100</span></div>
          <div style="font-size:10px;color:#aaa;margin-top:2px">Confidence · clinical + document</div>
        </div>''',unsafe_allow_html=True)

    st.markdown("<div style='margin-top:12px'></div>",unsafe_allow_html=True)

    # ── ACTION ZONE — always at top ─────────────────────────────────────────────
    sr = r.get("state_reason","")
    if state not in ["submitted","dismissed"]:
        st.markdown('<div class="action-zone">',unsafe_allow_html=True)
        st.markdown('<div style="font-size:10px;font-weight:600;color:#aaa;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:10px">Coordinator action</div>',unsafe_allow_html=True)
        bannermap = {
            "blocked": f'<div class="block-banner" style="margin-bottom:12px">🚫 <strong>Blocked</strong> — {sr}</div>',
            "needs_review": f'<div class="warn-banner" style="margin-bottom:12px">⚠ <strong>Needs review</strong> — {sr}</div>',
            "ready_to_submit": f'<div class="ready-banner" style="margin-bottom:12px">✓ <strong>Ready to submit</strong> — {sr}</div>'
        }
        if state in bannermap: st.markdown(bannermap[state],unsafe_allow_html=True)

        def do_reeval():
            nr,ns = next_result(cid)
            case["result"]=nr; case["state"]=nr["state"]; case["stage"]=ns
            case["eval_history"].append({"time":datetime.now(),"score":nr["confidence_score"],"state":nr["state"]})
            st.rerun()
        def do_dismiss():
            case["state"]="dismissed"
            case["eval_history"].append({"time":datetime.now(),"score":score,"state":"dismissed"})
            st.rerun()

        if state=="blocked":
            ca,cb = st.columns([2,1])
            with ca:
                if st.button("Re-evaluate case",use_container_width=True,type="primary",key=f"re_{cid}"):
                    with st.spinner("Agent re-evaluating..."): time.sleep(1)
                    do_reeval()
            with cb:
                if st.button("Dismiss",use_container_width=True,key=f"di_{cid}"): do_dismiss()
            st.markdown('<div style="font-size:11px;color:#bbb;margin-top:6px">Submit not available while Blocked — resolve gaps and re-evaluate.</div>',unsafe_allow_html=True)

        elif state=="needs_review":
            ca,cb,cc = st.columns(3)
            with ca:
                if st.button("Re-evaluate case",use_container_width=True,type="secondary",key=f"re_{cid}"):
                    with st.spinner("Agent re-evaluating..."): time.sleep(1)
                    do_reeval()
            with cb:
                if st.button("Submit — log reason",use_container_width=True,type="primary",key=f"su_{cid}"):
                    st.session_state[f"sr_{cid}"] = True
            with cc:
                if st.button("Dismiss",use_container_width=True,key=f"di_{cid}"): do_dismiss()
            if st.session_state.get(f"sr_{cid}"):
                st.markdown("<div style='margin-top:10px'></div>",unsafe_allow_html=True)
                reason = st.text_area("Why are you submitting despite the review flag? (required)",
                    placeholder="e.g. ESI confirmed verbally with physician — documentation pending sync.",
                    key=f"rt_{cid}",label_visibility="visible")
                if st.button("Confirm and submit",type="primary",key=f"cf_{cid}"):
                    if not reason.strip(): st.error("Please enter a reason before submitting.")
                    else:
                        case["override_reason"]=reason; case["state"]="submitted"
                        case["eval_history"].append({"time":datetime.now(),"score":score,"state":"submitted"})
                        del st.session_state[f"sr_{cid}"]
                        st.rerun()

        elif state=="ready_to_submit":
            ca,cb = st.columns([3,1])
            with ca:
                if st.button("Confirm and submit to payer",use_container_width=True,type="primary",key=f"su_{cid}"):
                    case["state"]="submitted"
                    case["eval_history"].append({"time":datetime.now(),"score":score,"state":"submitted"})
                    st.rerun()
            with cb:
                if st.button("Dismiss",use_container_width=True,key=f"di_{cid}"): do_dismiss()
        st.markdown("</div>",unsafe_allow_html=True)
    else:
        bmap = {"submitted":f'<div class="sub-banner">📤 <strong>Submitted to payer</strong> — Case closed.{(" Override logged: "+case.get("override_reason","")) if case.get("override_reason") else ""}</div>',"dismissed":'<div class="sub-banner">✕ <strong>Dismissed</strong> — Closed without submission.</div>'}
        if state in bmap: st.markdown(bmap[state],unsafe_allow_html=True)

    # ── WHAT TO DO NEXT — second priority ──────────────────────────────────────
    todo = r.get("what_to_do",[])
    if todo and state not in ["submitted","dismissed","ready_to_submit"]:
        st.markdown('<div class="detail-card">',unsafe_allow_html=True)
        st.markdown('<div class="dct">What to do next</div>',unsafe_allow_html=True)
        for s in todo:
            st.markdown(f'''<div style="display:flex;align-items:flex-start;gap:10px;padding:8px 0;border-bottom:1px solid #f5f5f3">
              <div style="width:22px;height:22px;border-radius:50%;background:#1D9E75;color:white;font-size:11px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px">{s["step"]}</div>
              <div><div style="font-size:11px;font-weight:600;color:#666;margin-bottom:2px">{s["who"]}</div>
              <div style="font-size:12px;color:#444;line-height:1.6">{s["action"]}</div></div>
            </div>''',unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

    # ── CRITERIA + DOCUMENTS side by side ──────────────────────────────────────
    cl,cr = st.columns(2)
    with cl:
        st.markdown('<div class="detail-card">',unsafe_allow_html=True)
        st.markdown('<div class="dct">Criteria check</div>',unsafe_allow_html=True)
        for c in r.get("criteria",[]):
            ic = "✓" if c["status"]=="met" else ("✗" if c["status"]=="not_met" else "!")
            col = "#1D9E75" if c["status"]=="met" else ("#E24B4A" if c["status"]=="not_met" else "#EF9F27")
            tc = "st-clin" if c["signal_type"]=="clinical" else "st-doc"
            tl = "Clinical" if c["signal_type"]=="clinical" else "Document"
            ah = f'<div style="font-size:11px;color:#E24B4A;margin-top:3px;line-height:1.5">→ {c["action"]}</div>' if c.get("action") and c["status"]!="met" else ""
            st.markdown(f'''<div style="display:flex;align-items:flex-start;gap:8px;padding:7px 0;border-bottom:1px solid #f5f5f3">
              <div style="color:{col};font-weight:700;font-size:13px;width:15px;flex-shrink:0;margin-top:1px">{ic}</div>
              <div style="flex:1">
                <div style="font-size:12px;font-weight:600;color:#222;margin-bottom:1px">{c["name"]}</div>
                <div style="font-size:11px;color:#666;line-height:1.5">{c["detail"]}</div>{ah}
              </div>
              <span class="sig-tag {tc}" style="flex-shrink:0;margin-top:2px">{tl}</span>
            </div>''',unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)
    with cr:
        docs = r.get("docs",{})
        st.markdown('<div class="detail-card">',unsafe_allow_html=True)
        st.markdown('<div class="dct">Document audit — from EHR</div>',unsafe_allow_html=True)
        for dn,di in docs.items():
            if di["status"]=="valid": ic,bg,tc="✓","#E1F5EE","#085041"
            elif di["status"]=="stale": ic,bg,tc="!","#FAEEDA","#633806"
            else: ic,bg,tc="✗","#FCEBEB","#791F1F"
            st.markdown(f'''<div style="display:flex;align-items:flex-start;gap:10px;padding:8px 0;border-bottom:1px solid #f5f5f3">
              <div style="width:24px;height:24px;border-radius:6px;background:{bg};display:flex;align-items:center;justify-content:center;font-weight:700;color:{tc};flex-shrink:0;font-size:12px">{ic}</div>
              <div><div style="font-size:12px;font-weight:600;color:#222;margin-bottom:2px">{dn}</div>
              <div style="font-size:11px;color:#888;line-height:1.5">{di["detail"]}</div></div>
            </div>''',unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

    # ── COLLAPSIBLE — codes + history + PA letter ──────────────────────────────
    with st.expander("ICD-10 · CPT codes · Evaluation history"):
        st.markdown('<div style="font-size:11px;font-weight:600;color:#aaa;text-transform:uppercase;letter-spacing:0.04em;margin-bottom:8px">Codes</div>',unsafe_allow_html=True)
        for code in r.get("icd10_codes",[]): st.markdown(f'<span class="sig-tag st-clin" style="margin:2px 4px 2px 0;display:inline-block">{code}</span>',unsafe_allow_html=True)
        for code in r.get("cpt_codes",[]): st.markdown(f'<span class="sig-tag st-doc" style="margin:2px 4px 2px 0;display:inline-block">{code}</span>',unsafe_allow_html=True)
        st.markdown("<div style='margin-top:14px'></div>",unsafe_allow_html=True)
        st.markdown('<div style="font-size:11px;font-weight:600;color:#aaa;text-transform:uppercase;letter-spacing:0.04em;margin-bottom:8px">Evaluation history</div>',unsafe_allow_html=True)
        icons={"blocked":"🔴","needs_review":"🟡","ready_to_submit":"🟢","submitted":"📤","dismissed":"⚫"}
        for ev in reversed(case.get("eval_history",[])[-5:]):
            st.markdown(f'<div class="hist-item">{icons.get(ev["state"],"⚪")} &nbsp;{slabel(ev["state"])} &nbsp;·&nbsp; score {ev["score"]} &nbsp;·&nbsp; {fmt(ev["time"])}</div>',unsafe_allow_html=True)

    if state in ["needs_review","ready_to_submit"] and r.get("pa_letter"):
        with st.expander("Preview PA letter — drafted by agent"):
            st.text(r["pa_letter"])

# ── New case ───────────────────────────────────────────────────────────────────
def new_case():
    st.markdown('<p style="font-size:13px;font-weight:600;color:#111;margin-bottom:4px">New case — EHR intake</p>',unsafe_allow_html=True)
    st.markdown('<p style="font-size:11px;color:#888;margin-bottom:16px">In production, cases arrive automatically from the EHR. Select a test case below to simulate EHR intake.</p>',unsafe_allow_html=True)
    loaded = set(st.session_state.cases.keys())
    unloaded = [tc for tc in TEST_CASES if tc["id"] not in loaded]
    if not unloaded:
        st.success("All 6 test cases are loaded in the queue.")
        if st.button("Reset — clear all cases",type="secondary"):
            st.session_state.cases={}; st.rerun()
        return
    opts = [f"{tc['id']} — {tc['name']}, {tc['age_gender']} — {tc['diagnosis']}" for tc in unloaded]
    sel = st.selectbox("Select case from EHR",opts)
    tc = unloaded[opts.index(sel)]
    c1,c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="detail-card"><div class="dct">Patient</div><div style="font-size:12px;color:#444;line-height:2.1"><b>Name:</b> {tc["name"]}<br><b>Age/Gender:</b> {tc["age_gender"]}<br><b>Payer:</b> {tc["payer"]}<br><b>Physician:</b> {tc["physician"]}<br><b>Facility:</b> {tc["facility"]}</div></div>',unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="detail-card"><div class="dct">Procedure</div><div style="font-size:12px;color:#444;line-height:2.1"><b>Diagnosis:</b> {tc["diagnosis"]}<br><b>Treatment:</b> {tc["treatment"]}</div></div>',unsafe_allow_html=True)
    ca,cb = st.columns([2,1])
    with ca:
        if st.button("Send to agent — evaluate this case",type="primary",use_container_width=True):
            with st.spinner("Agent evaluating..."): time.sleep(1.2)
            load_case(tc)
            r2 = st.session_state.cases[tc["id"]]["result"]
            st.success(f"Done — {slabel(r2['state'])} · Score {r2['confidence_score']}")
            if st.button("View in queue →"): st.session_state.screen="listing"; st.rerun()
    with cb:
        if st.button("Load all 6 cases",use_container_width=True):
            with st.spinner("Loading..."): time.sleep(1.5)
            for t in TEST_CASES:
                if t["id"] not in st.session_state.cases: load_case(t)
            st.session_state.screen="listing"; st.rerun()

# ── Policy ─────────────────────────────────────────────────────────────────────
def policy():
    st.markdown('<p style="font-size:13px;font-weight:600;color:#111;margin-bottom:4px">Policy documents</p>',unsafe_allow_html=True)
    st.markdown('<p style="font-size:11px;color:#888;margin-bottom:16px">In production, payer policy PDFs are stored in ChromaDB and retrieved by the agent on every evaluation. Demo mode uses pre-loaded criteria.</p>',unsafe_allow_html=True)
    st.markdown('''<div class="detail-card"><div class="dct">Loaded — UHC Lumbar Surgery 2024</div>
    <div style="font-size:12px;color:#444;line-height:2">
      <b>Payer:</b> UnitedHealthcare PPO<br>
      <b>Specialty:</b> Spine — lumbar decompression<br>
      <b>CPT codes:</b> 63047, 63048, 63030<br>
      <b>Key criteria:</b> MRI within 12 months · PT 12+ sessions with documented failure · At least 1 failed ESI · Symptoms 6+ weeks · Board-certified surgeon<br>
      <b>Status:</b> Active · Last updated Jan 2024
    </div></div>''',unsafe_allow_html=True)

# ── Router ─────────────────────────────────────────────────────────────────────
nav()
st.markdown("<hr style='border:none;border-top:1px solid #e8e8e4;margin:0 0 18px'>",unsafe_allow_html=True)
{"listing":listing,"detail":detail,"new_case":new_case,"policy":policy}.get(st.session_state.screen, listing)()
