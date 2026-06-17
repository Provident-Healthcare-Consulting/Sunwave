import json, math, os, pandas as pd
from datetime import datetime, timezone

# ── Load general report data ──────────────────────────────────────────────────
with open('report_data.json', 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

DATE_FIELDS = {
    'Census': 'Admission Date', 'Census Active': 'Admission Date',
    'Census_Admitted': 'Admission Date', 'Census_Discharge': 'Discharge Date',
    'GroupNotes': 'session_date', 'Incident Report': 'incident_reports.date_of_incident',
    'Opportunities Active': 'created_on', 'Opportunities by Created Date': 'created_on',
    'Opportunities': 'created_on', 'Patients': 'created_on',
    'Payment Report Payment Date': 'payment_date', 'Payment Report Deposit Date': 'deposit_date',
    'Referral Active': 'created_on', 'Report Auth': 'admission_date',
    'Report Deleted Form': 'deleted_on', 'Report Diagnois Changes': 'date_from',
    'Report Form Modified': 'modified_on', 'Report Program Change': 'start_on',
    'Report UR Changes': 'admission_date', 'Users': 'created_on',
}
tab_config = {}
for sheet, info in raw_data.items():
    dc = DATE_FIELDS.get(sheet, '')
    tab_config[sheet] = info['columns'].index(dc) if dc and dc in info['columns'] else -1

# ── Load billing data ─────────────────────────────────────────────────────────
df = pd.read_excel('MASTER_Sunwave_New_PowerQuerry.xlsx', sheet_name='Payment Report Deposit Date')
df['deposit_date'] = pd.to_datetime(df['deposit_date'], errors='coerce')
for c in ['line_charge_amount','line_paid_amount','line_adjusted','line_allocated_amount','line_allowed']:
    df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

billing_rows = []
for _, r in df.iterrows():
    dep = r['deposit_date']
    billing_rows.append({
        'deposit_date': dep.strftime('%m/%d/%Y') if pd.notna(dep) else '',
        'payer_name': str(r['payer_name']) if pd.notna(r['payer_name']) else '',
        'level_of_care': str(r['level_of_care']) if pd.notna(r['level_of_care']) else '',
        'adjustment_type': str(r['adjustment_type']) if pd.notna(r['adjustment_type']) else '',
        'service_facility': str(r['service_facility']) if pd.notna(r['service_facility']) else '',
        'service_name': str(r['service_name']) if pd.notna(r['service_name']) else '',
        'payment_type': str(r['payment_type']) if pd.notna(r['payment_type']) else '',
        'line_charge_amount': round(float(r['line_charge_amount']), 2),
        'line_paid_amount': round(float(r['line_paid_amount']), 2),
        'line_adjusted': round(float(r['line_adjusted']), 2),
        'line_allocated_amount': round(float(r['line_allocated_amount']), 2),
        'line_patient_name': str(r['line_patient_name']) if pd.notna(r['line_patient_name']) else '',
        'procedure_code': str(r['procedure_code']) if pd.notna(r['procedure_code']) else '',
    })

# ── Load census data ─────────────────────────────────────────────────────────
cdf = pd.read_excel('MASTER_Sunwave_New_PowerQuerry.xlsx', sheet_name='Census')
cdf['Admission Date'] = pd.to_datetime(cdf['Admission Date'], errors='coerce')
cdf['Discharge Date'] = pd.to_datetime(cdf['Discharge Date'], errors='coerce')
cdf['Age']            = pd.to_numeric(cdf['Age'], errors='coerce')
cdf['Length Of Stay'] = pd.to_numeric(cdf['Length Of Stay'], errors='coerce')

census_rows = []
for _, r in cdf.iterrows():
    adm = r['Admission Date']; dis = r['Discharge Date']
    census_rows.append({
        'adm':   adm.strftime('%m/%d/%Y') if pd.notna(adm) else '',
        'dis':   dis.strftime('%m/%d/%Y') if pd.notna(dis) else '',
        'loc':   str(r['Admission Level Of Care']).strip() if pd.notna(r['Admission Level Of Care']) else '',
        'cloc':  str(r['Current Level Of Care']).strip()   if pd.notna(r['Current Level Of Care'])   else '',
        'gen':   str(r['Patient Gender Code']).strip()     if pd.notna(r['Patient Gender Code'])     else '',
        'age':   int(r['Age']) if pd.notna(r['Age']) else None,
        'drug':  str(r['Primary Drug Of Choice ']).strip() if pd.notna(r['Primary Drug Of Choice ']) else '',
        'ref':   str(r['Referral Source']).strip()         if pd.notna(r['Referral Source'])         else '',
        'dtype': str(r['Discharge Type']).strip()          if pd.notna(r['Discharge Type'])          else '',
        'los':   int(r['Length Of Stay']) if pd.notna(r['Length Of Stay']) else None,
        'name':  str(r['Patient Name']).strip()            if pd.notna(r['Patient Name'])            else '',
    })

# ── Opportunities data (Marketing + Opportunities sections) ──────────────────
odf = pd.read_excel('MASTER_Sunwave_New_PowerQuerry.xlsx', sheet_name='Opportunities by Created Date')
odf['created_on']    = pd.to_datetime(odf['created_on'],    errors='coerce')
odf['admission_date']= pd.to_datetime(odf['admission_date'],errors='coerce')
opp_rows = []
for _, r in odf.iterrows():
    co = r['created_on']; ad = r['admission_date']
    oid = r['opportunity_id']
    opp_rows.append({
        'id':          '' if pd.isna(oid) else str(int(oid)) if isinstance(oid,(int,float)) else str(oid).strip(),
        'co':          co.strftime('%m/%d/%Y') if pd.notna(co) else '',
        'adm':         ad.strftime('%m/%d/%Y') if pd.notna(ad) and ad.year>2000 else '',
        'outcome':     str(r['outcome']).strip()           if pd.notna(r['outcome'])            else '',
        'stage':       str(r['stage']).strip()             if pd.notna(r['stage'])              else '',
        'loc':         str(r['level_of_care']).strip()     if pd.notna(r['level_of_care'])      else '',
        'ins':         str(r['insurance provider']).strip()if pd.notna(r['insurance provider']) else '',
        'ref':         str(r['referral name']).strip()     if pd.notna(r['referral name'])      else '',
        'lost_r':      str(r['lost reason']).strip()       if pd.notna(r['lost reason'])        else '',
        'aband_r':     str(r['abandoned reason']).strip()  if pd.notna(r['abandoned reason'])   else '',
        'name':        str(r['patient name']).strip()      if pd.notna(r['patient name'])       else '',
    })

# ── Timeline data (Opportunity expand/collapse) ──────────────────────────────
tldf = pd.read_excel('MASTER_Sunwave_New_PowerQuerry.xlsx', sheet_name='Timeline')
tldf['activity_date'] = pd.to_datetime(tldf['activity_date'], errors='coerce')
timeline_rows = []
for _, r in tldf.iterrows():
    ad = r['activity_date']
    oid = r['opportunity_id']
    timeline_rows.append({
        'oid':     '' if pd.isna(oid) else str(int(oid)) if isinstance(oid,(int,float)) else str(oid).strip(),
        'date':    ad.strftime('%m/%d/%Y %I:%M %p') if pd.notna(ad) else '',
        'subject': str(r['task_subject']).strip()    if pd.notna(r['task_subject'])    else '',
        'type':    str(r['type']).strip()            if pd.notna(r['type'])            else '',
        'by':      str(r['created_by_name']).strip() if pd.notna(r['created_by_name']) else '',
        'wf':      str(r['workflow_status']).strip() if pd.notna(r['workflow_status']) else '',
        'text':    str(r['text']).strip()            if pd.notna(r['text'])            else '',
        'sortKey': ad.timestamp() if pd.notna(ad) else 0,
    })

# ── Report Auth data (Utilization Review) ────────────────────────────────────
adf = pd.read_excel('MASTER_Sunwave_New_PowerQuerry.xlsx', sheet_name='Report Auth')
adf['admission_date']  = pd.to_datetime(adf['admission_date'],  errors='coerce')
adf['next_review_date']= pd.to_datetime(adf['next_review_date'],errors='coerce')
for c in ['authorized_units','billed_units_total']:
    adf[c] = pd.to_numeric(adf[c], errors='coerce').fillna(0)
auth_rows = []
for _, r in adf.iterrows():
    ad = r['admission_date']; nrd = r['next_review_date']
    auth_rows.append({
        'adm':      ad.strftime('%m/%d/%Y')  if pd.notna(ad)  else '',
        'nrd':      nrd.strftime('%m/%d/%Y') if pd.notna(nrd) else '',
        'code':     str(r['authorization_code']).strip() if pd.notna(r['authorization_code']) else '',
        'au':       round(float(r['authorized_units']), 1),
        'bu':       round(float(r['billed_units_total']), 1),
        'ins':      str(r['insurance_provider']).strip()  if pd.notna(r['insurance_provider'])  else '',
        'reviewer': str(r['ur_reviewer']).strip()         if pd.notna(r['ur_reviewer'])         else '',
        'patient':  str(r['patient_name']).strip()        if pd.notna(r['patient_name'])        else '',
        'facility': str(r['service_facility']).strip()    if pd.notna(r['service_facility'])    else '',
    })

# ── Census_Admitted data (Operations) ────────────────────────────────────────
opdf = pd.read_excel('MASTER_Sunwave_New_PowerQuerry.xlsx', sheet_name='Census_Admitted')
opdf['Admission Date'] = pd.to_datetime(opdf['Admission Date'], errors='coerce')
ops_rows = []
for _, r in opdf.iterrows():
    ad = r['Admission Date']
    at = r.get('Admission Time')
    hr = at.hour if (pd.notna(at) if not isinstance(at, float) else False) and hasattr(at,'hour') else -1
    dow_pandas = int(ad.dayofweek) if pd.notna(ad) else -1   # 0=Mon pandas → convert to JS 0=Sun later
    ops_rows.append({
        'date':      ad.strftime('%m/%d/%Y') if pd.notna(ad) else '',
        'hour':      hr,
        'dow':       (dow_pandas + 1) % 7 if dow_pandas >= 0 else -1,  # JS 0=Sun
        'rep':       str(r['Admissions Rep']).strip()          if pd.notna(r['Admissions Rep'])        else '',
        'therapist': str(r['Assigned Therapist']).strip()      if pd.notna(r['Assigned Therapist'])    else '',
        'ins':       str(r['Insurance Name']).strip()          if pd.notna(r['Insurance Name'])        else '',
        'loc':       str(r['Admission Level Of Care']).strip() if pd.notna(r['Admission Level Of Care']) else '',
        'name':      str(r['Patient Name']).strip()            if pd.notna(r['Patient Name'])          else '',
    })

# ── GroupNotes data (Clinical) ───────────────────────────────────────────────
gndf = pd.read_excel('MASTER_Sunwave_New_PowerQuerry.xlsx', sheet_name='GroupNotes')
gndf['session_date'] = pd.to_datetime(gndf['session_date'], errors='coerce')
gndf['length_time']  = pd.to_numeric(gndf['length_time'],  errors='coerce').fillna(0)
gnotes_rows = []
for _, r in gndf.iterrows():
    sd = r['session_date']
    gnotes_rows.append({
        'date':   sd.strftime('%m/%d/%Y') if pd.notna(sd) else '',
        'title':  str(r['group_title']).strip() if pd.notna(r['group_title']) else '',
        'status': str(r['status']).strip()      if pd.notna(r['status'])      else '',
        'mins':   int(r['length_time']),
    })

# ── CRM Task data ────────────────────────────────────────────────────────────
try:
    ctdf = pd.read_excel('MASTER_Sunwave_New_PowerQuerry.xlsx', sheet_name='CRM Task')
    for _c in ['activity_date','task_due_date','reminder_date_time','created_on','orig_activity_date']:
        if _c in ctdf.columns:
            ctdf[_c] = pd.to_datetime(ctdf[_c], errors='coerce')
    def _fmt_dt(v):
        if pd.isna(v): return ''
        try: return v.strftime('%m/%d/%Y %I:%M %p')
        except Exception: return ''
    crm_task_rows = []
    for _, r in ctdf.iterrows():
        ad = r.get('activity_date'); dd = r.get('task_due_date'); rm = r.get('reminder_date_time')
        crm_task_rows.append({
            'id':         '' if pd.isna(r.get('id','')) else str(r.get('id','')).strip(),
            'aid':        '' if pd.isna(r.get('Associated_id','')) else str(r.get('Associated_id','')).strip(),
            'assoc':      str(r.get('associated_with','')).strip()  if pd.notna(r.get('associated_with',''))  else '',
            'subject':    str(r.get('task_subject','')).strip()     if pd.notna(r.get('task_subject',''))     else '',
            'type':       str(r.get('type','')).strip()             if pd.notna(r.get('type',''))             else '',
            'task_type':  str(r.get('task_type','')).strip()        if pd.notna(r.get('task_type',''))        else '',
            'status':     str(r.get('task_status','')).strip()      if pd.notna(r.get('task_status',''))      else '',
            'created_by': str(r.get('created_by_name','')).strip()  if pd.notna(r.get('created_by_name',''))  else '',
            'assigned':   str(r.get('assigned_to_name','')).strip() if pd.notna(r.get('assigned_to_name','')) else '',
            'text':       str(r.get('text','')).strip()             if pd.notna(r.get('text',''))             else '',
            'activity':   _fmt_dt(ad),
            'due':        _fmt_dt(dd),
            'reminder':   _fmt_dt(rm),
            'sortKey':    ad.timestamp() if pd.notna(ad) else 0,
        })
except Exception as _e:
    print(f"Warning: could not load CRM Task sheet: {_e}")
    crm_task_rows = []

# ── Referral Active data ─────────────────────────────────────────────────────
try:
    rdf = pd.read_excel('MASTER_Sunwave_New_PowerQuerry.xlsx', sheet_name='Referral Active')
    rdf['created_on'] = pd.to_datetime(rdf['created_on'], errors='coerce')
    referral_rows = []
    for _, r in rdf.iterrows():
        co = r['created_on']
        rid = r.get('referral_id', r.get('id', ''))
        referral_rows.append({
            'id':       '' if pd.isna(rid) else str(int(rid)) if isinstance(rid,(int,float)) else str(rid).strip(),
            'co':       co.strftime('%m/%d/%Y') if pd.notna(co) else '',
            'name':     str(r.get('referral name','') or r.get('name','')).strip(),
            'type':     str(r.get('referral type','')).strip() if pd.notna(r.get('referral type','')) else '',
            'stage':    str(r.get('referral source stage','')).strip() if pd.notna(r.get('referral source stage','')) else '',
            'owner':    str(r.get('referral_source_owner','')).strip() if pd.notna(r.get('referral_source_owner','')) else '',
            'city':     str(r.get('referral source city','')).strip() if pd.notna(r.get('referral source city','')) else '',
            'state':    str(r.get('referral source state','')).strip() if pd.notna(r.get('referral source state','')) else '',
        })
except Exception as _e:
    print(f"Warning: could not load Referral Active sheet: {_e}")
    referral_rows = []

# ── Build metadata ───────────────────────────────────────────────────────────
build_info_js = json.dumps({'refreshed_at': datetime.now(timezone.utc).isoformat()})

# ── Serialize ─────────────────────────────────────────────────────────────────
general_js  = json.dumps(raw_data,     separators=(',',':'), ensure_ascii=True).replace('</', '<\\/')
config_js   = json.dumps(tab_config,   separators=(',',':'))
billing_js  = json.dumps(billing_rows, separators=(',',':'), ensure_ascii=True).replace('</', '<\\/')
census_js   = json.dumps(census_rows,  separators=(',',':'), ensure_ascii=True).replace('</', '<\\/')
opp_js      = json.dumps(opp_rows,     separators=(',',':'), ensure_ascii=True).replace('</', '<\\/')
auth_js     = json.dumps(auth_rows,    separators=(',',':'), ensure_ascii=True).replace('</', '<\\/')
ops_js      = json.dumps(ops_rows,     separators=(',',':'), ensure_ascii=True).replace('</', '<\\/')
gnotes_js   = json.dumps(gnotes_rows,  separators=(',',':'), ensure_ascii=True).replace('</', '<\\/')
timeline_js = json.dumps(timeline_rows,separators=(',',':'), ensure_ascii=True).replace('</', '<\\/')
referral_js = json.dumps(referral_rows,separators=(',',':'), ensure_ascii=True).replace('</', '<\\/')
crm_task_js = json.dumps(crm_task_rows,separators=(',',':'), ensure_ascii=True).replace('</', '<\\/')

# ── CSS ───────────────────────────────────────────────────────────────────────
CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body { height: 100%; }
body { font-family: Arial, sans-serif; background: #eaecf0; color: #333; font-size: 13px; display: flex; flex-direction: column; overflow: hidden; }

/* ── Layout ── */
#app { display: flex; flex: 1; overflow: hidden; }
#sidebar {
  width: 210px; min-width: 210px;
  background: linear-gradient(180deg, #0f2540 0%, #1a3a5c 100%);
  display: flex; flex-direction: column;
  overflow: hidden; box-shadow: 3px 0 12px rgba(0,0,0,.45);
  z-index: 10;
}
#content { flex: 1; overflow-y: auto; background: #eaecf0; }

/* ── Sidebar header ── */
.sb-header {
  padding: 16px 14px 10px;
  border-bottom: 1px solid rgba(255,255,255,.1);
  background: rgba(0,0,0,.2);
}
.sb-header h1 { color: #fff; font-size: 14px; font-weight: 700; line-height: 1.3; }
.sb-header p  { color: #8ab0d0; font-size: 10px; margin-top: 2px; }

/* ── Refresh button ── */
.refresh-btn {
  margin: 10px 10px 6px;
  padding: 8px 10px;
  width: calc(100% - 20px);
  background: linear-gradient(to bottom, #2e7d32, #1b5e20);
  border: 1px solid #145214;
  border-bottom: 3px solid #0d3b0d;
  border-radius: 6px;
  color: #fff;
  font-size: 11px; font-weight: 700; letter-spacing: .4px;
  cursor: pointer; text-align: center;
  box-shadow: 0 4px 8px rgba(0,0,0,.5), inset 0 1px 0 rgba(255,255,255,.2);
  transition: all .15s; text-transform: uppercase;
}
.refresh-btn:hover  { background: linear-gradient(to bottom, #388e3c, #2e7d32); transform: translateY(-1px); box-shadow: 0 6px 10px rgba(0,0,0,.5), inset 0 1px 0 rgba(255,255,255,.25); }
.refresh-btn:active { background: linear-gradient(to bottom, #1b5e20, #0d3b0d); transform: translateY(2px); box-shadow: 0 1px 3px rgba(0,0,0,.5), inset 0 2px 4px rgba(0,0,0,.4); border-bottom-width: 1px; }

/* ── Nav scroll area ── */
.sb-nav { flex: 1; overflow-y: auto; padding: 4px 0 12px; }
.sb-nav::-webkit-scrollbar { width: 4px; }
.sb-nav::-webkit-scrollbar-thumb { background: rgba(255,255,255,.2); border-radius: 2px; }

/* ── Section labels ── */
.sb-section {
  color: #6a99bf; font-size: 10px; font-weight: 700; letter-spacing: 1px;
  text-transform: uppercase; padding: 10px 14px 4px; user-select: none;
}

/* ── 3D Nav buttons ── */
.nav-item {
  display: block; width: calc(100% - 16px); margin: 3px 8px;
  padding: 9px 12px;
  background: linear-gradient(to bottom, #254e78, #1a3a5c);
  border: 1px solid #0f2540;
  border-bottom: 3px solid #0a1c30;
  border-radius: 6px;
  color: #c8dff0;
  font-size: 11.5px; font-weight: 600;
  cursor: pointer; text-align: left;
  box-shadow: 0 4px 6px rgba(0,0,0,.45), inset 0 1px 0 rgba(255,255,255,.12);
  transition: all .15s;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.nav-item:hover {
  background: linear-gradient(to bottom, #336699, #254e78);
  color: #fff;
  box-shadow: 0 6px 10px rgba(0,0,0,.5), inset 0 1px 0 rgba(255,255,255,.18);
  transform: translateY(-1px);
}
.nav-item:active {
  background: linear-gradient(to bottom, #1a3a5c, #0f2540);
  transform: translateY(2px);
  box-shadow: 0 1px 3px rgba(0,0,0,.5), inset 0 2px 4px rgba(0,0,0,.35);
  border-bottom-width: 1px;
}
.nav-item.active {
  background: linear-gradient(to bottom, #1a6ec0, #1252a0);
  border-color: #0d3f7a; border-bottom-color: #082d58;
  color: #fff;
  box-shadow: 0 2px 4px rgba(0,0,0,.5), inset 0 2px 4px rgba(0,0,0,.25), inset 0 1px 0 rgba(255,255,255,.15);
  transform: translateY(1px);
}

/* ── Page header ── */
.page-header {
  background: linear-gradient(135deg, #1a3a5c 0%, #1a6ec0 100%);
  color: #fff; padding: 12px 20px;
  display: flex; align-items: center; justify-content: space-between;
}
.page-header h2 { font-size: 16px; font-weight: 700; }
.page-header small { font-size: 11px; opacity: .75; }
.main { padding: 14px 18px; }

/* ── Controls bar ── */
.controls {
  background: #fff; border-radius: 8px; padding: 11px 14px;
  margin-bottom: 12px; display: flex; flex-wrap: wrap; align-items: center;
  gap: 10px; box-shadow: 0 1px 4px rgba(0,0,0,.1);
}
.view-btns { display: flex; gap: 4px; }
.view-btn {
  padding: 6px 15px;
  background: linear-gradient(to bottom, #ffffff, #e8edf2);
  border: 1px solid #aabcce; border-bottom: 2px solid #8aabbe;
  border-radius: 5px; color: #1a3a5c; font-size: 12px; font-weight: 700;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(0,0,0,.15), inset 0 1px 0 rgba(255,255,255,.9);
  transition: all .12s;
}
.view-btn:hover  { background: linear-gradient(to bottom, #f0f5fa, #dde6ef); transform: translateY(-1px); box-shadow: 0 3px 6px rgba(0,0,0,.2); }
.view-btn:active { transform: translateY(1px); box-shadow: 0 1px 2px rgba(0,0,0,.2); border-bottom-width: 1px; }
.view-btn.active {
  background: linear-gradient(to bottom, #1252a0, #1a6ec0);
  border-color: #0d3f7a; border-bottom-color: #082d58;
  color: #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,.4), inset 0 2px 3px rgba(0,0,0,.2);
  transform: translateY(1px);
}
.nav-btns { display: flex; align-items: center; gap: 8px; }
.period-nav-btn {
  padding: 5px 13px;
  background: linear-gradient(to bottom, #f5f7fa, #e0e8f0);
  border: 1px solid #b0c4d8; border-bottom: 2px solid #8aabbe;
  border-radius: 5px; font-size: 16px; font-weight: 900;
  cursor: pointer; color: #1a3a5c;
  box-shadow: 0 2px 4px rgba(0,0,0,.15), inset 0 1px 0 rgba(255,255,255,.9);
  transition: all .12s;
}
.period-nav-btn:hover  { background: linear-gradient(to bottom, #fff, #d0dce8); transform: translateY(-1px); }
.period-nav-btn:active { transform: translateY(1px); border-bottom-width: 1px; box-shadow: inset 0 2px 3px rgba(0,0,0,.15); }
.period-label {
  font-weight: 700; font-size: 13px; min-width: 175px; text-align: center;
  color: #1a3a5c; background: #eef3f9;
  padding: 5px 12px; border-radius: 5px;
  border: 1px solid #c5d8ec;
}
.date-input  { padding: 5px 9px; border: 1px solid #ccc; border-radius: 5px; font-size: 12px; }
.search-box  { padding: 6px 10px; border: 1px solid #ccc; border-radius: 5px; font-size: 12px; flex: 1; min-width: 160px; }
.export-btn {
  padding: 7px 15px;
  background: linear-gradient(to bottom, #2e9c5a, #217346);
  border: 1px solid #185a35; border-bottom: 2px solid #0f3d24;
  border-radius: 5px; color: #fff; font-size: 12px; font-weight: 700;
  cursor: pointer;
  box-shadow: 0 2px 5px rgba(0,0,0,.25), inset 0 1px 0 rgba(255,255,255,.2);
  transition: all .12s; white-space: nowrap;
}
.export-btn:hover  { background: linear-gradient(to bottom, #39b86a, #2e9c5a); transform: translateY(-1px); box-shadow: 0 3px 7px rgba(0,0,0,.3); }
.export-btn:active { transform: translateY(1px); border-bottom-width: 1px; box-shadow: inset 0 2px 3px rgba(0,0,0,.2); }

/* ── Stat / KPI cards ── */
.stats-bar  { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 12px; }
.stat-card  {
  background: #fff; border-radius: 8px; padding: 13px 18px;
  min-width: 130px; flex: 1;
  box-shadow: 0 2px 6px rgba(0,0,0,.1);
  border-left: 4px solid #1a3a5c;
  transition: transform .15s, box-shadow .15s;
}
.stat-card:hover { transform: translateY(-2px); box-shadow: 0 4px 10px rgba(0,0,0,.15); }
.stat-card.green  { border-left-color: #217346; }
.stat-card.orange { border-left-color: #c86a00; }
.stat-card.purple { border-left-color: #6a3a9c; }
.stat-card .val { font-size: 24px; font-weight: 700; color: #1a3a5c; line-height: 1.2; }
.stat-card .lbl { font-size: 11px; color: #777; margin-top: 3px; text-transform: uppercase; letter-spacing: .4px; }

/* ── Spot table (billing) ── */
.spot-wrap  { background: #fff; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,.1); overflow: auto; margin-bottom: 16px; }
.spot-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.spot-table thead th { background: #1a3a5c; color: #fff; padding: 9px 14px; text-align: center; white-space: nowrap; font-weight: 600; }
.spot-table thead th:first-child { text-align: left; }
.spot-table tbody tr { border-bottom: 1px solid #eee; }
.spot-table tbody tr:hover { background: #f0f5fb; }
.spot-table tbody tr:nth-child(even) { background: #fafbfd; }
.spot-table tbody tr:nth-child(even):hover { background: #f0f5fb; }
.spot-table td { padding: 8px 14px; white-space: nowrap; }
.spot-table td.metric-name { font-weight: 600; }
.spot-table td.num { text-align: right; font-variant-numeric: tabular-nums; color: #1a3a5c; }

/* ── Break / trend grid ── */
.break-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 14px; }
.break-card { background: #fff; border-radius: 8px; padding: 13px 15px; box-shadow: 0 1px 4px rgba(0,0,0,.1); }
.break-card h3 { font-size: 12px; font-weight: 700; color: #1a3a5c; margin-bottom: 8px; }
.break-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.break-table thead th { background: #eef3f9; color: #1a3a5c; padding: 7px 10px; text-align: left; font-weight: 700; border-bottom: 2px solid #c5d8ec; }
.break-table tbody tr { border-bottom: 1px solid #eee; }
.break-table tbody tr:hover { background: #f0f5fb; }
.break-table td { padding: 6px 10px; }
.break-table td.num { text-align: right; }
.break-table tr.total-row td { font-weight: 700; border-top: 2px solid #ccc; background: #f5f8fc; }
.trend-wrap { background: #fff; border-radius: 8px; padding: 13px 15px; box-shadow: 0 1px 4px rgba(0,0,0,.1); overflow: auto; margin-bottom: 14px; }
.trend-wrap h3 { font-size: 12px; font-weight: 700; color: #1a3a5c; margin-bottom: 8px; }
.trend-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.trend-table thead th { background: #1a3a5c; color: #fff; padding: 8px 14px; text-align: center; white-space: nowrap; }
.trend-table thead th:first-child { text-align: left; }
.trend-table tbody tr { border-bottom: 1px solid #eee; }
.trend-table tbody tr:hover { background: #f0f5fb; }
.trend-table tbody tr:nth-child(even) { background: #fafbfd; }
.trend-table td { padding: 7px 14px; white-space: nowrap; }
.trend-table td.metric-name { font-weight: 600; }
.trend-table td.num { text-align: right; }

/* ── Data table ── */
.table-wrap { background: #fff; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,.1); overflow: auto; max-height: 480px; }
table { width: 100%; border-collapse: collapse; font-size: 12px; }
thead th { background: #1a3a5c; color: #fff; padding: 8px 10px; text-align: left; position: sticky; top: 0; z-index: 2; white-space: nowrap; font-weight: 600; cursor: pointer; user-select: none; }
thead th:hover { background: #244d73; }
tbody tr { border-bottom: 1px solid #eee; }
tbody tr:hover { background: #edf3fa; }
tbody td { padding: 6px 10px; max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
tbody tr:nth-child(even) { background: #fafbfd; }
.no-data { text-align: center; padding: 40px; color: #999; font-size: 14px; }
.pagination { display: flex; align-items: center; gap: 6px; margin-top: 10px; flex-wrap: wrap; }
.page-info { font-size: 12px; color: #666; margin-right: 4px; }
.page-btn { padding: 4px 10px; border: 1px solid #ccc; background: #fff; border-radius: 4px; cursor: pointer; font-size: 11px; }
.page-btn:hover { background: #eee; }
.page-btn.active { background: #1a3a5c; color: #fff; border-color: #1a3a5c; }

h2.section-title {
  font-size: 13px; font-weight: 700; color: #1a3a5c;
  margin: 16px 0 8px; padding-bottom: 5px;
  border-bottom: 2px solid #1a3a5c;
}
.date-field-label { font-size: 11px; color: #999; font-style: italic; }
.spot-section { background: #1a3a5c; color: #fff; font-weight: 700; font-size: 11px; padding: 6px 14px; letter-spacing: .4px; text-transform: uppercase; }
/* Heatmap */
.heatmap-wrap { overflow-x: auto; background:#fff; border-radius:8px; padding:14px; box-shadow:0 1px 4px rgba(0,0,0,.1); margin-bottom:14px; }
.heatmap-table { border-collapse:collapse; font-size:11px; }
.heatmap-table th { padding:5px 8px; background:#1a3a5c; color:#fff; white-space:nowrap; text-align:center; }
.heatmap-table th.row-hdr { background:#eef3f9; color:#1a3a5c; text-align:right; }
.heatmap-table td { width:38px; height:26px; text-align:center; border:1px solid #e0e6ee; font-size:11px; font-weight:600; cursor:default; }
.hm-0{background:#f5f8fc;color:#999}.hm-1{background:#d4e8fb;color:#1a3a5c}.hm-2{background:#a8d0f7;color:#1a3a5c}.hm-3{background:#6fb5f0;color:#fff}.hm-4{background:#3694e0;color:#fff}.hm-5{background:#1a6ec0;color:#fff}.hm-6{background:#0d3f7a;color:#fff}
/* Funnel */
.funnel-bar { display:flex; align-items:center; gap:10px; margin:4px 0; }
.funnel-label { width:120px; text-align:right; font-size:12px; font-weight:600; color:#333; }
.funnel-track { flex:1; background:#eef3f9; border-radius:4px; height:22px; position:relative; overflow:hidden; }
.funnel-fill { height:100%; border-radius:4px; background:linear-gradient(to right,#1a6ec0,#3694e0); transition:width .4s; }
.funnel-val { position:absolute; right:8px; top:3px; font-size:11px; font-weight:700; color:#fff; }
.funnel-val.dark { color:#1a3a5c; }

/* ════════════════════════════════════════════════════════════════
   STRIVE-MATCHED LAYOUT — DM Sans + Space Mono, navy / teal palette
═══════════════════════════════════════════════════════════════ */
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600;700&display=swap');
:root {
  --navy:#0a3d5c; --teal:#3dffc0; --teal-dim:rgba(61,255,192,0.12);
  --bg:#f4f6f9; --white:#fff; --border:#e1e7ef;
  --text:#2D2D2D; --muted:#6b7e96;
  --sky:#4BBDE8;
  --red:#ef4444; --amber:#f59e0b; --blue:#3b82f6; --green:#10b981; --purple:#8b5cf6;
  --shadow:0 1px 3px rgba(10,61,92,.07),0 4px 14px rgba(10,61,92,.04);
  --shadow-h:0 4px 12px rgba(10,61,92,.11),0 8px 28px rgba(10,61,92,.07);
}
body {
  font-family: 'DM Sans', system-ui, -apple-system, 'Segoe UI', sans-serif !important;
  background: var(--bg) !important; color: var(--text) !important; font-size: 13px !important;
}
#app { display: flex !important; flex-direction: column !important; flex: 1; overflow: hidden; }

#topbar {
  background: var(--navy);
  color: #fff; height: 58px; flex-shrink: 0; z-index: 200;
  display: flex; align-items: center; gap: 16px; padding: 0 28px;
  box-shadow: 0 2px 16px rgba(10,61,92,.25);
  border-bottom: none;
}
.brand { display: flex; align-items: center; gap: 14px; line-height: 1.15; }
.brand-pill {
  background: var(--teal); color: var(--navy);
  font-family: 'Space Mono', monospace; font-size: 11px; font-weight: 700;
  letter-spacing: .08em; padding: 5px 10px; border-radius: 4px;
}
.brand-text { display: flex; flex-direction: column; }
.brand .name { font-size: 15px; font-weight: 600; color: #fff; letter-spacing: .2px; }
.brand .sub  { font-size: 11px; color: rgba(255,255,255,.4); font-family: 'Space Mono', monospace; font-weight: 400; }

/* Tab nav — separate white bar below the navy topbar */
#tabBar {
  background: var(--white); border-bottom: 1px solid var(--border);
  padding: 0 28px; display: flex; flex-wrap: wrap; row-gap: 0;
  position: sticky; top: 58px; z-index: 190;
  box-shadow: 0 2px 8px rgba(10,61,92,.05);
  height: auto; flex-shrink: 0;
}
.tab-btn {
  padding: 12px 14px; border: none;
  border-bottom: 3px solid transparent;
  background: none;
  font-family: 'DM Sans', sans-serif; font-size: 12.5px; font-weight: 500;
  color: var(--muted); cursor: pointer; white-space: nowrap;
  transition: all .2s; margin-bottom: -1px; height: auto; border-radius: 0;
  display: inline-flex; align-items: center;
}
.tab-btn:hover { color: var(--navy); background: none; }
.tab-btn.active {
  color: var(--navy); border-bottom-color: var(--teal);
  font-weight: 700; background: none;
}
.tab-btn.tab-hidden { display: none; }
.topbar-action {
  padding: 6px 14px; background: rgba(255,255,255,.07); color: #fff;
  border: 1px solid rgba(255,255,255,.13); border-radius: 6px;
  font-family: 'DM Sans', sans-serif; font-size: 12px; font-weight: 500; cursor: pointer;
  display: inline-flex; align-items: center; gap: 6px; transition: all .2s;
  height: 32px;
}
.topbar-action:hover { background: rgba(255,255,255,.13); border-color: rgba(255,255,255,.25); }

#main { flex: 1; display: flex; overflow: hidden; }
#filterRail {
  width: 240px; flex-shrink: 0;
  background: #fff; border-right: 1px solid var(--border);
  padding: 18px 14px; overflow-y: auto;
  box-shadow: 2px 0 12px rgba(10,61,92,.04);
}
#filterRail h3 {
  font-family: 'Space Mono', monospace;
  font-size: 9px; font-weight: 700; color: var(--muted);
  letter-spacing: .12em; text-transform: uppercase;
  margin-bottom: 14px; padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}
#filterRail .filter-section { display: none; }
#filterRail .filter-section.active { display: block; }
#filterRail .filter-section .controls {
  background: transparent !important; box-shadow: none !important;
  padding: 0 !important; margin: 0 !important;
  display: flex !important; flex-direction: column !important;
  gap: 14px !important;
}
#filterRail .filter-section .view-btns { display: grid !important; grid-template-columns: repeat(3, 1fr); gap: 5px; width: 100%; }
#filterRail .filter-section .view-btn {
  padding: 7px 8px !important; font-family: 'Space Mono', monospace !important;
  font-size: 10px !important; font-weight: 700 !important; letter-spacing: .04em !important;
  border-radius: 6px !important; border: 1px solid var(--border) !important;
  background: #fff !important; color: var(--muted) !important;
  text-transform: uppercase !important; box-shadow: none !important; transform: none !important;
}
#filterRail .filter-section .view-btn.active { background: var(--navy) !important; color: #fff !important; border-color: var(--navy) !important; }
#filterRail .filter-section .view-btn:hover:not(.active) { background: rgba(10,61,92,.07); color: var(--navy) !important; }
#filterRail .filter-section .nav-btns { display: flex; align-items: center; gap: 5px; width: 100%; }
#filterRail .filter-section .period-nav-btn {
  padding: 5px 10px !important; font-family: 'Space Mono', monospace !important;
  font-size: 13px !important; border: 1px solid var(--border) !important;
  background: #fff !important; color: var(--navy) !important; border-radius: 5px !important;
  box-shadow: none !important; transform: none !important;
}
#filterRail .filter-section .period-nav-btn:hover { background: var(--navy) !important; color: #fff !important; }
#filterRail .filter-section .period-label {
  flex: 1; min-width: 0 !important;
  font-family: 'Space Mono', monospace !important; font-size: 11px !important;
  padding: 5px 7px !important; background: #fff !important;
  border: 1px solid var(--border) !important; color: var(--navy) !important;
  text-align: center;
}
#filterRail .filter-section .date-input,
#filterRail .filter-section select.date-input {
  width: 100% !important;
  font-family: 'Space Mono', monospace !important; font-size: 11px !important;
  padding: 6px 8px !important; border: 1px solid var(--border) !important;
  border-radius: 5px !important; color: var(--navy) !important; background: #fff !important;
}
#filterRail .filter-section .search-box {
  width: 100% !important;
  font-family: 'DM Sans', sans-serif !important; font-size: 12px !important;
  padding: 8px 11px !important; border: 1px solid var(--border) !important;
  border-radius: 6px !important; background: #fff !important;
}
#filterRail .filter-section .search-box:focus,
#filterRail .filter-section .date-input:focus { outline: none; border-color: var(--navy) !important; }
#filterRail .filter-section .export-btn {
  width: 100% !important;
  background: linear-gradient(135deg, var(--navy), #1e5e85) !important;
  border: none !important; color: #fff !important;
  font-family: 'DM Sans', sans-serif !important; font-size: 11px !important;
  font-weight: 700 !important; padding: 8px 14px !important;
  border-radius: 6px !important; box-shadow: none !important; transform: none !important;
}
#filterRail .filter-section .export-btn:hover {
  background: linear-gradient(135deg, var(--teal), var(--navy)) !important;
}

#content { flex: 1; overflow-y: auto; background: var(--bg); }
.page-header {
  background: #fff !important; padding: 16px 28px !important;
  display: flex; align-items: center; justify-content: space-between;
  border-bottom: 1px solid var(--border); color: var(--text) !important;
  position: sticky; top: 0; z-index: 100;
  box-shadow: 0 2px 8px rgba(10,61,92,.05);
}
.page-header h2 { font-size: 17px !important; font-weight: 700 !important; color: var(--navy) !important; letter-spacing: -.2px; }
.page-header small {
  font-size: 11px !important; color: var(--muted) !important; opacity: 1 !important;
  font-family: 'Space Mono', monospace !important;
}
.page-actions { display: flex; gap: 8px; }
.page-action-btn {
  font-family: 'DM Sans', sans-serif !important;
  padding: 7px 14px; font-size: 11.5px; font-weight: 700;
  background: #fff; color: var(--navy);
  border: 1px solid var(--border); border-radius: 6px;
  cursor: pointer; display: inline-flex; align-items: center; gap: 6px;
  transition: all .15s; letter-spacing: .02em;
}
.page-action-btn:hover { background: var(--navy); color: #fff; border-color: var(--navy); }
.page-action-btn.green {
  background: linear-gradient(135deg, #10b981, #059669); border: none; color: #fff;
}
.page-action-btn.green:hover { background: linear-gradient(135deg, #3dffc0, #10b981); transform: translateY(-1px); }
.page-action-btn.blue {
  background: linear-gradient(135deg, var(--navy), #1e5e85); border: none; color: #fff;
}
.page-action-btn.blue:hover { background: linear-gradient(135deg, var(--teal), var(--navy)); transform: translateY(-1px); }

/* KPI cards (Strive-matched) */
.stats-bar { gap: 14px !important; }
.stat-card {
  background: var(--white) !important; border: 1px solid var(--border) !important;
  border-radius: 12px !important; padding: 16px 20px !important;
  box-shadow: var(--shadow) !important; position: relative; overflow: hidden;
  border-left: none !important;
}
.stat-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
  border-radius: 12px 12px 0 0; background: var(--navy);
}
.stat-card.green::before  { background: var(--green); }
.stat-card.orange::before { background: var(--amber); }
.stat-card.purple::before { background: var(--purple); }
.stat-card .lbl {
  font-family: 'Space Mono', monospace !important;
  font-size: 9px !important; letter-spacing: .1em !important;
  text-transform: uppercase; color: var(--muted) !important; margin-top: 0 !important;
}
.stat-card .val {
  font-size: 28px !important; font-weight: 700 !important; color: var(--navy) !important;
  line-height: 1; letter-spacing: -.03em; margin-bottom: 7px;
}

/* Tables (Strive-matched) */
.spot-wrap, .trend-wrap, .break-card, .table-wrap, .heatmap-wrap {
  background: var(--white) !important; border: 1px solid var(--border) !important;
  border-radius: 14px !important; box-shadow: var(--shadow) !important;
  padding: 18px !important;
}
.break-card h3, .trend-wrap h3 {
  font-size: 13px !important; font-weight: 700 !important; color: var(--navy) !important;
  margin-bottom: 14px !important;
}
.spot-table thead th, .trend-table thead th, table thead th {
  background: var(--white) !important; color: var(--muted) !important;
  font-family: 'Space Mono', monospace !important;
  font-size: 9px !important; letter-spacing: .08em !important;
  text-transform: uppercase; font-weight: 700 !important;
  padding: 10px 14px !important; border-bottom: 1px solid var(--border) !important;
}
.spot-table thead th:first-child, .trend-table thead th:first-child { text-align: left; }
.break-table thead th {
  background: var(--white) !important; color: var(--muted) !important;
  font-family: 'Space Mono', monospace !important;
  font-size: 9px !important; letter-spacing: .08em !important; text-transform: uppercase !important;
  font-weight: 700 !important; border-bottom: 1px solid var(--border) !important;
}
.spot-table tbody tr, .trend-table tbody tr, .break-table tbody tr, table tbody tr {
  border-bottom: 1px solid rgba(225,231,239,.5) !important;
}
.spot-table tbody tr:nth-child(even), .trend-table tbody tr:nth-child(even),
table tbody tr:nth-child(even) { background: transparent !important; }
.spot-table tbody tr:hover, .trend-table tbody tr:hover,
.break-table tbody tr:hover, table tbody tr:hover { background: rgba(244,246,249,.8) !important; }
.spot-section {
  background: var(--navy) !important; color: var(--teal) !important;
  font-family: 'Space Mono', monospace !important; font-weight: 700 !important;
  font-size: 10px !important; letter-spacing: .08em !important;
}
h2.section-title {
  font-size: 13px !important; font-weight: 700 !important; color: var(--navy) !important;
  border-bottom: 1px solid var(--border) !important;
  font-family: 'DM Sans', sans-serif !important;
  text-transform: uppercase; letter-spacing: .04em;
}

/* Tab settings dropdown */
.tabs-menu {
  position: absolute; top: 64px; right: 28px; background: #fff;
  border: 1px solid var(--border); border-radius: 8px;
  box-shadow: 0 8px 28px rgba(10,61,92,.18);
  padding: 10px 0; min-width: 240px; max-height: 460px; overflow-y: auto;
  z-index: 250; display: none;
}
.tabs-menu.open { display: block; }
.tabs-menu-header {
  font-family: 'Space Mono', monospace; font-size: 9px; font-weight: 700;
  color: var(--muted); text-transform: uppercase; letter-spacing: .12em;
  padding: 4px 14px 8px; border-bottom: 1px solid #f3f4f6;
}
.tabs-menu label {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 14px; font-size: 12px; color: var(--text);
  cursor: pointer; user-select: none; font-family: 'DM Sans', sans-serif;
}
.tabs-menu label:hover { background: rgba(244,246,249,.8); }
.tabs-menu input { margin: 0; }
.tabs-menu .actions { padding: 8px 14px 4px; border-top: 1px solid #f3f4f6; display: flex; gap: 6px; }
.tabs-menu .actions button {
  flex: 1; padding: 6px 8px; font-family: 'Space Mono', monospace;
  font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .04em;
  background: #fff; color: var(--navy); border: 1px solid var(--border); border-radius: 5px; cursor: pointer;
}
.tabs-menu .actions button:hover { background: var(--navy); color: #fff; }

/* ── Mobile responsive ── */
@media (max-width: 1024px) {
  body { overflow: auto; }
  #app { overflow: visible; }
  #main { flex-direction: column; overflow: visible; }
  #content { overflow: visible; }
  #filterRail {
    width: 100%; border-right: none;
    border-bottom: 1px solid var(--border);
    padding: 10px 16px;
    position: sticky; top: 0; z-index: 150;
    background: #fff;
    box-shadow: 0 2px 8px rgba(10,61,92,.06);
    overflow: visible;
  }
  #filterRail h3 { display: none; }
  #filterRail .filter-section.active .controls {
    flex-direction: row !important; flex-wrap: wrap !important;
    gap: 8px !important; align-items: center !important;
  }
  #filterRail .filter-section .view-btns { display: flex !important; gap: 4px; }
  #filterRail .filter-section .view-btn { padding: 5px 7px !important; font-size: 9px !important; }
  #filterRail .filter-section .period-label { min-width: 110px !important; font-size: 10px !important; }
  #filterRail .filter-section .search-box { width: auto !important; min-width: 140px !important; }
  #filterRail .filter-section .date-input,
  #filterRail .filter-section select.date-input { width: auto !important; }
  #filterRail .filter-section .export-btn { width: auto !important; }
  .break-grid { grid-template-columns: 1fr !important; }
}
"""

# ── JavaScript ────────────────────────────────────────────────────────────────
JS = r"""
/* ===== Build info ===== */
const BUILD_INFO = (function(){try{return JSON.parse(document.getElementById('buildInfo').textContent);}catch(e){return{};}})();

/* ===== Data ===== */
let RAW      = JSON.parse(document.getElementById('generalData').textContent);
let DATE_IDX = JSON.parse(document.getElementById('dateIdx').textContent);
let BROWS    = JSON.parse(document.getElementById('billingData').textContent);
let SHEETS   = Object.keys(RAW);

/* ===== Navigation state ===== */
let curPage = 'billing';
let gView={}, gOffset={}, gSearch={}, gDate={}, gSort={};
const PAGE_SIZE = 100;
SHEETS.forEach(s=>{
  gView[s]='month'; gOffset[s]=0; gSearch[s]=''; gDate[s]=null; gSort[s]={col:-1,asc:true};
});
let bNavView='all', bNavDate=null, bNavSearch='', bSortCol='deposit_date', bSortAsc=false;
for(const r of BROWS){ const d=pd(r.deposit_date); if(d){bNavDate=d;break;} }
if(!bNavDate) bNavDate=new Date();

/* ===== Helpers ===== */
function pd(str){
  if(!str||str===''||str==='nan')return null;
  const m=str.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})/);
  if(m){const d=new Date(+m[3],+m[1]-1,+m[2]);d.setHours(0,0,0,0);return d;}
  return null;
}
function fd(d){ if(!d)return''; return String(d.getMonth()+1).padStart(2,'0')+'/'+String(d.getDate()).padStart(2,'0')+'/'+d.getFullYear(); }
function fmtMoney(v){ return '$'+Math.round(+v||0).toLocaleString(); }
function fmtPct(v){ if(!v||isNaN(v)||!isFinite(v))return'0.0%'; return(v*100).toFixed(1)+'%'; }
function fmtAvg(v){ if(!v||isNaN(v)||!isFinite(v))return'$0.00'; return'$'+v.toFixed(2); }
function esc(s){ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function gwk(d){const c=new Date(d);c.setDate(c.getDate()-c.getDay());c.setHours(0,0,0,0);return c;}
function smm(a,b){return a.getFullYear()===b.getFullYear()&&a.getMonth()===b.getMonth();}
function swk(a,b){return gwk(a).getTime()===gwk(b).getTime();}
function sdy(a,b){return a.getFullYear()===b.getFullYear()&&a.getMonth()===b.getMonth()&&a.getDate()===b.getDate();}

function fmtSyncedAt(tsMs){
  try{
    const d=tsMs?new Date(tsMs):(BUILD_INFO.refreshed_at?new Date(BUILD_INFO.refreshed_at):null);
    if(!d||isNaN(d))return'';
    const DAYS=['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
    const MONS=['January','February','March','April','May','June','July','August','September','October','November','December'];
    const h=d.getHours(),m=d.getMinutes(),ap=h>=12?'PM':'AM',h12=h%12===0?12:h%12;
    return'Synced: '+DAYS[d.getDay()]+', '+MONS[d.getMonth()]+' '+d.getDate()+', '+d.getFullYear()+' · '+String(h12).padStart(2,'0')+':'+String(m).padStart(2,'0')+' '+ap;
  }catch(e){return'';}
}

/* ===== Sidebar nav ===== */
function showPage(id){
  curPage=id;
  document.querySelectorAll('.tab-btn,.nav-item').forEach(b=>b.classList.remove('active'));
  const btn=document.getElementById('btn-'+id.replace(/[^a-zA-Z0-9]/g,'_'));
  if(btn) btn.classList.add('active');
  document.querySelectorAll('.page-section').forEach(s=>s.style.display='none');
  const sec=document.getElementById('sec-'+id.replace(/[^a-zA-Z0-9]/g,'_'));
  if(sec){ sec.style.display='block'; const c=document.getElementById('content'); if(c) c.scrollTop=0; }
  // Move section controls into filter rail
  populateFilterRail(id, sec);
  // Update header
  const titles={
    'billing':'AR / Billing Dashboard',
    'census':'Census Dashboard \u2014 Strive Fort Wayne, IN',
    'marketing':'Marketing Dashboard',
    'opportunities':'Opportunities Detail',
    'referral':'Referral Active',
    'crmtask':'CRM Tasks',
    'ur':'Utilization Review',
    'clinical':'Clinical \u2014 Group Notes',
    'operations':'Operations Dashboard',
    'fieldexplorer':'Field Explorer',
  };
  const subs={
    'billing':'Payment Report Deposit Date',
    'census':'Census',
    'marketing':'Opportunities by Created Date',
    'opportunities':'Opportunities by Created Date',
    'referral':'Referral Active + Timeline',
    'crmtask':'CRM Task',
    'ur':'Report Auth',
    'clinical':'GroupNotes',
    'operations':'Census_Admitted',
    'fieldexplorer':'Census',
  };
  const specialPages=new Set(['billing','census','marketing','opportunities','referral','crmtask','ur','clinical','operations','fieldexplorer']);
  document.getElementById('pageTitle').textContent = titles[id]||id;
  const _sync=fmtSyncedAt();
  document.getElementById('pageSub').textContent = _sync || (subs[id]||'');
  if(!specialPages.has(id)) renderGeneral(id);
}

function doRefresh(){
  const btn=document.querySelector('[title="Refresh data"]');
  if(btn) btn.textContent='Refreshing…';
  setTimeout(()=>{
    if(curPage==='billing'){ renderBillingSpot();renderBillingBreakdowns();renderBillingTrend();renderBillingDetail(); }
    else if(curPage==='census'){ renderCensusSpot();renderCensusTrend();renderCensusBreakdowns(); }
    else if(curPage==='marketing'){ renderMarketingSpot();renderMarketingTrend();renderMarketingDetail(); }
    else if(curPage==='opportunities'){ renderOpportunities(); }
    else if(curPage==='referral'){ renderReferrals(); }
    else if(curPage==='crmtask'){ renderCRMTask(); }
    else if(curPage==='ur'){ renderURSpot();renderURTrend(); }
    else if(curPage==='clinical'){ renderClinicalSpot();renderClinical(); }
    else if(curPage==='operations'){ renderOpsHeatmap();renderOpsDetail();renderOpsMonthlyIns(); }
    else if(curPage==='fieldexplorer'){ renderFieldExplorer(); }
    else renderGeneral(curPage);
    if(btn) btn.innerHTML='&#8635;&nbsp; Refresh';
  },100);
}

/* ═══════════════════════════════════════════════════════════════
   BILLING LOGIC
═══════════════════════════════════════════════════════════════ */
const TODAY=new Date(); TODAY.setHours(0,0,0,0);
function daysAgo(n){const d=new Date(TODAY);d.setDate(d.getDate()-n);return d;}
function som(d){return new Date(d.getFullYear(),d.getMonth(),1);}
function eom(d){return new Date(d.getFullYear(),d.getMonth()+1,0);}

function bFilter(rows,from,to){
  return rows.filter(r=>{const d=pd(r.deposit_date);return d&&d>=from&&d<=to;});
}
function bMetrics(rows){
  const pr=rows.filter(r=>r.adjustment_type==='Allowed');
  const paid=pr.reduce((s,r)=>s+r.line_paid_amount,0);
  const charged=rows.reduce((s,r)=>s+r.line_charge_amount,0);
  const allowed=pr.reduce((s,r)=>s+r.line_allocated_amount,0);
  const contractual=rows.filter(r=>r.adjustment_type==='Contractual').reduce((s,r)=>s+r.line_adjusted,0);
  const writeoff=rows.filter(r=>r.adjustment_type==='Write Off'||r.adjustment_type==='Administrative Write Off').reduce((s,r)=>s+r.line_adjusted,0);
  const noncov=rows.filter(r=>r.adjustment_type==='Non Covered Service').reduce((s,r)=>s+r.line_charge_amount,0);
  const lines=pr.length;
  return{paid,charged,allowed,contractual,writeoff,noncov,lines,
    cr:allowed>0?paid/allowed:0,nr:charged>0?paid/charged:0,avg:lines>0?paid/lines:0};
}
const BPERIODS=[
  {label:'Today',from:TODAY,to:TODAY},
  {label:'Yesterday',from:daysAgo(1),to:daysAgo(1)},
  {label:'Last 7 Days',from:daysAgo(6),to:TODAY},
  {label:'Last 31 Days',from:daysAgo(30),to:TODAY},
  {label:'Last 90 Days',from:daysAgo(89),to:TODAY},
  {label:'Last 12 Mo',from:daysAgo(364),to:TODAY},
  {label:'YTD',from:new Date(TODAY.getFullYear(),0,1),to:TODAY},
];
const BMETRICS=[
  {key:'lines',      label:'# Payment Lines',                    fmt:v=>v.toLocaleString()},
  {key:'charged',    label:'Charged $',                          fmt:fmtMoney},
  {key:'allowed',    label:'Allowed $ (contractual)',             fmt:fmtMoney},
  {key:'paid',       label:'Paid $',                             fmt:fmtMoney},
  {key:'contractual',label:'Contractual Adjustments $',           fmt:fmtMoney},
  {key:'writeoff',   label:'Write-Offs $',                       fmt:fmtMoney},
  {key:'noncov',     label:'Non-Covered / Denied $',             fmt:fmtMoney},
  {key:'cr',         label:'Collection Rate (Paid \u00f7 Allowed)',fmt:fmtPct},
  {key:'nr',         label:'Net Realization (Paid \u00f7 Charged)',fmt:fmtPct},
  {key:'avg',        label:'Avg $ / Line',                       fmt:fmtAvg},
];

function renderBillingSpot(){
  let h='<table class="spot-table"><thead><tr><th>Metric</th>';
  BPERIODS.forEach(p=>h+='<th>'+p.label+'</th>');
  h+='</tr></thead><tbody>';
  BMETRICS.forEach(m=>{
    h+='<tr><td class="metric-name">'+m.label+'</td>';
    BPERIODS.forEach(p=>{const c=bMetrics(bFilter(BROWS,p.from,p.to));h+='<td class="num">'+m.fmt(c[m.key])+'</td>';});
    h+='</tr>';
  });
  h+='</tbody></table>';
  document.getElementById('bSpotTable').innerHTML=h;
}

function bNavLabel(){
  if(bNavView==='all')  return 'All Time';
  if(bNavView==='year') return String(bNavDate.getFullYear());
  if(bNavView==='month')return bNavDate.toLocaleString('default',{month:'long'})+' '+bNavDate.getFullYear();
  if(bNavView==='week'){const ws=gwk(bNavDate),we=new Date(ws);we.setDate(we.getDate()+6);return fd(ws)+' \u2013 '+fd(we);}
  return fd(bNavDate);
}
function bNavRange(){
  if(bNavView==='all')  return{from:new Date(1900,0,1),to:new Date(2100,0,1)};
  if(bNavView==='year') return{from:new Date(bNavDate.getFullYear(),0,1),to:new Date(bNavDate.getFullYear(),11,31)};
  if(bNavView==='month')return{from:som(bNavDate),to:eom(bNavDate)};
  if(bNavView==='week'){const ws=gwk(bNavDate),we=new Date(ws);we.setDate(we.getDate()+6);return{from:ws,to:we};}
  const d=new Date(bNavDate);return{from:d,to:d};
}
function bNavigate(dir){
  if(bNavView==='all') return;
  if(bNavView==='year') bNavDate=new Date(bNavDate.getFullYear()+dir,0,1);
  else if(bNavView==='month')bNavDate=new Date(bNavDate.getFullYear(),bNavDate.getMonth()+dir,1);
  else if(bNavView==='week')bNavDate=new Date(bNavDate.getTime()+dir*7*86400000);
  else bNavDate=new Date(bNavDate.getTime()+dir*86400000);
  renderBillingPeriod();
}
function bSetView(v){bNavView=v;renderBillingPeriod();}
function bJump(val){if(!val)return;const p=val.split('-');bNavDate=new Date(+p[0],+p[1]-1,+p[2]);renderBillingPeriod();}

function gbg(rows,key,fn){
  const m={};
  rows.forEach(r=>{const k=r[key]||'(blank)';m[k]=(m[k]||0)+fn(r);});
  return Object.entries(m).sort((a,b)=>b[1]-a[1]);
}

function renderBillingBreakdowns(){
  const{from,to}=bNavRange();
  const rows=bFilter(BROWS,from,to);
  const pr=rows.filter(r=>r.adjustment_type==='Allowed');
  const totalPaid=pr.reduce((s,r)=>s+r.line_paid_amount,0);
  const totalCharged=rows.reduce((s,r)=>s+r.line_charge_amount,0);

  const mkPayerTable=()=>{
    const byP=gbg(pr,'payer_name',r=>r.line_paid_amount);
    const top=byP.slice(0,9),other=byP.slice(9);
    let h='<table class="break-table"><thead><tr><th>Payer</th><th>Paid $</th><th>Lines</th><th>% Total</th></tr></thead><tbody>';
    top.forEach(([k,v])=>{
      const ln=pr.filter(r=>r.payer_name===k).length;
      h+='<tr><td>'+esc(k)+'</td><td class="num">'+fmtMoney(v)+'</td><td class="num">'+ln+'</td><td class="num">'+(totalPaid>0?(v/totalPaid*100).toFixed(1)+'%':'0%')+'</td></tr>';
    });
    if(other.length){const ov=other.reduce((s,[,v])=>s+v,0),ol=other.reduce((s,[k])=>s+pr.filter(r=>r.payer_name===k).length,0);
      h+='<tr><td><em>Others</em></td><td class="num">'+fmtMoney(ov)+'</td><td class="num">'+ol+'</td><td class="num">'+(totalPaid>0?(ov/totalPaid*100).toFixed(1)+'%':'0%')+'</td></tr>';}
    h+='<tr class="total-row"><td>Total</td><td class="num">'+fmtMoney(totalPaid)+'</td><td class="num">'+pr.length+'</td><td class="num">100%</td></tr></tbody></table>';
    return h;
  };
  const mkLocTable=()=>{
    const byL=gbg(pr,'level_of_care',r=>r.line_paid_amount);
    let h='<table class="break-table"><thead><tr><th>Level of Care</th><th>Paid $</th><th>Lines</th><th>% Total</th></tr></thead><tbody>';
    byL.forEach(([k,v])=>{
      const ln=pr.filter(r=>r.level_of_care===k).length;
      h+='<tr><td>'+esc(k)+'</td><td class="num">'+fmtMoney(v)+'</td><td class="num">'+ln+'</td><td class="num">'+(totalPaid>0?(v/totalPaid*100).toFixed(1)+'%':'0%')+'</td></tr>';
    });
    h+='<tr class="total-row"><td>Total</td><td class="num">'+fmtMoney(totalPaid)+'</td><td class="num">'+pr.length+'</td><td class="num">100%</td></tr></tbody></table>';
    return h;
  };
  const mkAdjTable=()=>{
    const ats=['Contractual','Non Covered Service','Write Off','Administrative Write Off'];
    let h='<table class="break-table"><thead><tr><th>Adjustment Type</th><th>Amount $</th><th>Lines</th><th>% Charged</th></tr></thead><tbody>';
    let tot=0;
    ats.forEach(at=>{
      const ar=rows.filter(r=>r.adjustment_type===at);
      const amt=ar.reduce((s,r)=>s+(at==='Non Covered Service'?r.line_charge_amount:r.line_adjusted),0);
      tot+=amt;
      h+='<tr><td>'+esc(at)+'</td><td class="num">'+fmtMoney(amt)+'</td><td class="num">'+ar.length+'</td><td class="num">'+(totalCharged>0?(amt/totalCharged*100).toFixed(1)+'%':'0%')+'</td></tr>';
    });
    h+='<tr class="total-row"><td>Total Written Off</td><td class="num">'+fmtMoney(tot)+'</td><td class="num">'+rows.filter(r=>r.adjustment_type!=='Allowed').length+'</td><td class="num">'+(totalCharged>0?(tot/totalCharged*100).toFixed(1)+'%':'0%')+'</td></tr></tbody></table>';
    return h;
  };
  document.getElementById('bPayerTable').innerHTML=mkPayerTable();
  document.getElementById('bLocTable').innerHTML=mkLocTable();
  document.getElementById('bAdjTable').innerHTML=mkAdjTable();
}

function renderBillingTrend(){
  const months=[];
  for(let i=5;i>=0;i--){const d=new Date(TODAY.getFullYear(),TODAY.getMonth()-i,1);months.push({label:d.toLocaleString('default',{month:'short',year:'2-digit'}),from:d,to:eom(d)});}
  const tm=[
    {label:'Paid $',fn:rs=>fmtMoney(rs.filter(r=>r.adjustment_type==='Allowed').reduce((s,r)=>s+r.line_paid_amount,0))},
    {label:'Charged $',fn:rs=>fmtMoney(rs.reduce((s,r)=>s+r.line_charge_amount,0))},
    {label:'# Lines',fn:rs=>rs.filter(r=>r.adjustment_type==='Allowed').length.toLocaleString()},
    {label:'Contractual Adj $',fn:rs=>fmtMoney(rs.filter(r=>r.adjustment_type==='Contractual').reduce((s,r)=>s+r.line_adjusted,0))},
    {label:'Non-Covered / Denied $',fn:rs=>fmtMoney(rs.filter(r=>r.adjustment_type==='Non Covered Service').reduce((s,r)=>s+r.line_charge_amount,0))},
    {label:'Avg $ / Line',fn:rs=>{const p=rs.filter(r=>r.adjustment_type==='Allowed');return fmtAvg(p.length>0?p.reduce((s,r)=>s+r.line_paid_amount,0)/p.length:0);}},
  ];
  let h='<table class="trend-table"><thead><tr><th>Metric</th>';
  months.forEach(m=>h+='<th>'+m.label+'</th>');
  h+='</tr></thead><tbody>';
  tm.forEach(m=>{
    h+='<tr><td class="metric-name">'+m.label+'</td>';
    months.forEach(mo=>{h+='<td class="num">'+m.fn(bFilter(BROWS,mo.from,mo.to))+'</td>';});
    h+='</tr>';
  });
  h+='</tbody></table>';
  document.getElementById('bTrendTable').innerHTML=h;
}

function renderBillingDetail(){
  const{from,to}=bNavRange();
  let rows=bFilter(BROWS,from,to);
  if(bNavSearch){const s=bNavSearch.toLowerCase();rows=rows.filter(r=>Object.values(r).some(v=>String(v).toLowerCase().includes(s)));}
  rows=rows.slice().sort((a,b)=>{
    const av=String(a[bSortCol]||''),bv=String(b[bSortCol]||'');
    const ad=pd(av),bd=pd(bv);
    if(ad&&bd)return bSortAsc?(ad-bd):(bd-ad);
    const an=parseFloat(av),bn=parseFloat(bv);
    if(!isNaN(an)&&!isNaN(bn))return bSortAsc?(an-bn):(bn-an);
    return bSortAsc?av.localeCompare(bv):bv.localeCompare(av);
  });
  const m=bMetrics(rows);
  document.getElementById('bKpiLines').textContent=m.lines.toLocaleString();
  document.getElementById('bKpiCharged').textContent=fmtMoney(m.charged);
  document.getElementById('bKpiPaid').textContent=fmtMoney(m.paid);
  document.getElementById('bKpiCR').textContent=fmtPct(m.cr);
  document.getElementById('bKpiNR').textContent=fmtPct(m.nr);
  document.getElementById('bKpiAvg').textContent=fmtAvg(m.avg);
  document.getElementById('bPeriodLabel').innerHTML=bNavLabel();
  document.getElementById('bViewMonth').className='view-btn'+(bNavView==='month'?' active':'');
  document.getElementById('bViewWeek').className='view-btn'+(bNavView==='week'?' active':'');
  document.getElementById('bViewDay').className='view-btn'+(bNavView==='day'?' active':'');
  document.getElementById('bViewYear').className='view-btn'+(bNavView==='year'?' active':'');
  document.getElementById('bViewAll').className='view-btn'+(bNavView==='all'?' active':'');

  const cols=['deposit_date','payer_name','level_of_care','adjustment_type','service_facility','service_name','line_patient_name','procedure_code','line_charge_amount','line_paid_amount','line_adjusted','line_allocated_amount'];
  const hdrs=['Deposit Date','Payer','Level of Care','Adj Type','Facility','Service','Patient','Code','Charged $','Paid $','Adjusted $','Allocated $'];
  const moneyIdx=new Set([8,9,10,11]);
  let h='<div class="table-wrap"><table><thead><tr>';
  cols.forEach((c,i)=>{const arr=bSortCol===c?(bSortAsc?' &#9650;':' &#9660;'):'';h+='<th onclick="bSetSort(\''+c+'\')" >'+hdrs[i]+arr+'</th>';});
  h+='</tr></thead><tbody>';
  const pg=rows.slice(0,200);
  if(!pg.length)h+='<tr><td colspan="'+cols.length+'" class="no-data">No records for selected period.</td></tr>';
  pg.forEach(r=>{h+='<tr>';cols.forEach((c,i)=>{const v=r[c];const disp=moneyIdx.has(i)?fmtMoney(+v):esc(v);h+='<td title="'+esc(v)+'">'+disp+'</td>';});h+='</tr>';});
  h+='</tbody></table></div>';
  if(rows.length>200)h+='<div class="page-info" style="margin-top:8px">Showing 200 of '+rows.length.toLocaleString()+' records — Export CSV for full data.</div>';
  document.getElementById('bDetailTable').innerHTML=h;
}

function bSetSort(col){if(bSortCol===col)bSortAsc=!bSortAsc;else{bSortCol=col;bSortAsc=false;}renderBillingDetail();renderBillingBreakdowns();}

function renderBillingPeriod(){ renderBillingBreakdowns(); renderBillingDetail(); }

function bExport(){
  const{from,to}=bNavRange();let rows=bFilter(BROWS,from,to);
  const cols=Object.keys(rows[0]||{});
  let csv=cols.map(c=>'"'+c+'"').join(',')+'\n';
  rows.forEach(r=>{csv+=cols.map(c=>'"'+String(r[c]||'').replace(/"/g,'""')+'"').join(',')+'\n';});
  const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv'}));
  a.download='billing_'+bNavLabel().replace(/[^a-z0-9]/gi,'_')+'.csv';a.click();
}

/* ═══════════════════════════════════════════════════════════════
   GENERAL REPORTS LOGIC
═══════════════════════════════════════════════════════════════ */
function gFilterRows(sheet){
  const info=RAW[sheet],dIdx=DATE_IDX[sheet],ref=gDate[sheet],view=gView[sheet],search=gSearch[sheet].toLowerCase();
  let rows=info.rows.filter(row=>{
    if(dIdx>=0&&ref){
      const d=pd(row[dIdx]);if(!d)return false;
      if(view==='month'&&!smm(d,ref))return false;
      if(view==='week'&&!swk(d,ref))return false;
      if(view==='day'&&!sdy(d,ref))return false;
    }
    if(search)return row.some(c=>String(c).toLowerCase().includes(search));
    return true;
  });
  const ss=gSort[sheet];
  if(ss.col>=0){rows=rows.slice().sort((a,b)=>{
    const av=String(a[ss.col]||''),bv=String(b[ss.col]||'');
    const ad=pd(av),bd=pd(bv);if(ad&&bd)return ss.asc?(ad-bd):(bd-ad);
    return ss.asc?av.localeCompare(bv):bv.localeCompare(av);
  });}
  return rows;
}
function gPeriodLabel(sheet){
  const ref=gDate[sheet],view=gView[sheet];
  if(!ref)return'All Dates';
  if(view==='month')return ref.toLocaleString('default',{month:'long'})+' '+ref.getFullYear();
  if(view==='week'){const ws=gwk(ref),we=new Date(ws);we.setDate(we.getDate()+6);return fd(ws)+' \u2013 '+fd(we);}
  return fd(ref);
}
function gNavigate(sheet,dir){
  const view=gView[sheet];let ref=new Date(gDate[sheet]||new Date());
  if(view==='month')ref=new Date(ref.getFullYear(),ref.getMonth()+dir,1);
  else if(view==='week')ref=new Date(ref.getTime()+dir*7*86400000);
  else ref=new Date(ref.getTime()+dir*86400000);
  gDate[sheet]=ref;gOffset[sheet]=0;renderGeneral(sheet);
}
function gSetView(sheet,view){
  gView[sheet]=view;gOffset[sheet]=0;
  if(!gDate[sheet]){const dIdx=DATE_IDX[sheet];if(dIdx>=0)for(const row of RAW[sheet].rows){const d=pd(row[dIdx]);if(d){gDate[sheet]=d;break;}}if(!gDate[sheet])gDate[sheet]=new Date();}
  renderGeneral(sheet);
}
function gSortCol(sheet,ci){const ss=gSort[sheet];if(ss.col===ci)ss.asc=!ss.asc;else{ss.col=ci;ss.asc=true;}gOffset[sheet]=0;renderGeneral(sheet);}
function gGotoPage(sheet,offset){gOffset[sheet]=Math.max(0,offset);renderGeneral(sheet);}
function gSearch2(sheet,val){gSearch[sheet]=val;gOffset[sheet]=0;renderGeneral(sheet);}
function gJump(sheet,val){if(!val)return;const p=val.split('-');gDate[sheet]=new Date(+p[0],+p[1]-1,+p[2]);gOffset[sheet]=0;renderGeneral(sheet);}
function gExport(sheet){
  const info=RAW[sheet],filtered=gFilterRows(sheet);
  let csv=info.columns.map(c=>'"'+c.replace(/"/g,'""')+'"').join(',')+'\n';
  filtered.forEach(row=>{csv+=row.map(c=>'"'+String(c||'').replace(/"/g,'""')+'"').join(',')+'\n';});
  const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv'}));
  a.download=sheet.replace(/[^a-z0-9]/gi,'_')+'.csv';a.click();
}

function renderGeneral(sheet){
  const sid=sheet.replace(/[^a-zA-Z0-9]/g,'_');
  const panel=document.getElementById('gpanel-'+sid);
  if(!panel)return;
  const info=RAW[sheet],cols=info.columns,dIdx=DATE_IDX[sheet],view=gView[sheet];
  const filtered=gFilterRows(sheet),offset=gOffset[sheet];
  const page=filtered.slice(offset,offset+PAGE_SIZE);
  const totalPages=Math.ceil(filtered.length/PAGE_SIZE);
  const curPage=Math.floor(offset/PAGE_SIZE)+1;

  // Stats
  let stats='<div class="stats-bar">';
  stats+='<div class="stat-card"><div class="val">'+filtered.length.toLocaleString()+'</div><div class="lbl">Total Records</div></div>';
  if(dIdx>=0){const ds=new Set();filtered.forEach(r=>{const d=pd(r[dIdx]);if(d)ds.add(fd(d));});stats+='<div class="stat-card green"><div class="val">'+ds.size+'</div><div class="lbl">Distinct Dates</div></div>';}
  const nIdx=cols.findIndex(c=>c.toLowerCase()==='patient name'||c.toLowerCase()==='patient_name'||c.toLowerCase()==='line_patient_name');
  if(nIdx>=0){const u=new Set(filtered.map(r=>r[nIdx]).filter(v=>v&&v!==''));stats+='<div class="stat-card orange"><div class="val">'+u.size+'</div><div class="lbl">Unique Patients</div></div>';}
  const fIdx=cols.findIndex(c=>c.toLowerCase().includes('service_facility')||c.toLowerCase()==='service facility');
  if(fIdx>=0){const u=new Set(filtered.map(r=>r[fIdx]).filter(v=>v&&v!==''));stats+='<div class="stat-card purple"><div class="val">'+u.size+'</div><div class="lbl">Facilities</div></div>';}
  stats+='</div>';

  const hasDate=dIdx>=0,dcn=hasDate?cols[dIdx]:'';
  let nav='';
  if(hasDate){
    nav='<div class="nav-btns">'
      +'<button class="period-nav-btn" onclick="gNavigate(\''+sid+'\',\''+sheet+'\',-1)">&#8249;</button>'
      +'<span class="period-label">'+gPeriodLabel(sheet)+'</span>'
      +'<button class="period-nav-btn" onclick="gNavigate(\''+sid+'\',\''+sheet+'\',1)">&#8250;</button>'
      +'</div>'
      +'<input type="date" class="date-input" title="Jump to date" onchange="gJump(\''+sheet+'\',this.value)">'
      +'<span class="date-field-label">by: '+esc(dcn)+'</span>';
  } else nav='<span class="period-label">All Dates</span>';

  let vbtns='';
  if(hasDate){
    vbtns='<div class="view-btns">'
      +'<button class="view-btn'+(view==='month'?' active':'')+'" onclick="gSetView(\''+sheet+'\',\'month\')">Month</button>'
      +'<button class="view-btn'+(view==='week' ?' active':'')+'" onclick="gSetView(\''+sheet+'\',\'week\')">Week</button>'
      +'<button class="view-btn'+(view==='day'  ?' active':'')+'" onclick="gSetView(\''+sheet+'\',\'day\')">Day</button>'
      +'</div>';
  }

  // Table
  let tbl='';
  if(!page.length){
    tbl='<div class="no-data">No records found for the selected period.</div>';
  } else {
    const ss=gSort[sheet];
    tbl='<div class="table-wrap"><table><thead><tr>';
    cols.forEach((c,i)=>{const arr=ss.col===i?(ss.asc?' &#9650;':' &#9660;'):'';tbl+='<th onclick="gSortCol(\''+sheet+'\','+i+')" title="Sort by '+esc(c)+'">'+esc(c)+arr+'</th>';});
    tbl+='</tr></thead><tbody>';
    page.forEach(row=>{tbl+='<tr>';row.forEach(cell=>{const v=esc(cell);tbl+='<td title="'+v+'">'+v+'</td>';});tbl+='</tr>';});
    tbl+='</tbody></table></div>';
  }

  // Pagination
  let pg='';
  if(totalPages>1){
    pg='<div class="pagination">';
    pg+='<span class="page-info">Showing '+(offset+1)+'\u2013'+Math.min(offset+PAGE_SIZE,filtered.length)+' of '+filtered.length.toLocaleString()+'</span>';
    if(curPage>1)pg+='<button class="page-btn" onclick="gGotoPage(\''+sheet+'\',0)">\u00ab</button>';
    if(curPage>1)pg+='<button class="page-btn" onclick="gGotoPage(\''+sheet+'\','+(offset-PAGE_SIZE)+')">\u2039</button>';
    for(let i=Math.max(0,curPage-3);i<Math.min(totalPages,curPage+2);i++)
      pg+='<button class="page-btn'+(i===curPage-1?' active':'')+'" onclick="gGotoPage(\''+sheet+'\','+(i*PAGE_SIZE)+')">'+(i+1)+'</button>';
    if(curPage<totalPages)pg+='<button class="page-btn" onclick="gGotoPage(\''+sheet+'\','+(offset+PAGE_SIZE)+')">\u203a</button>';
    if(curPage<totalPages)pg+='<button class="page-btn" onclick="gGotoPage(\''+sheet+'\','+((totalPages-1)*PAGE_SIZE)+')">\u00bb</button>';
    pg+='</div>';
  }

  panel.innerHTML='<div class="controls">'+vbtns+nav
    +'<input type="text" class="search-box" placeholder="Search all columns..." value="'+esc(gSearch[sheet])+'" oninput="gSearch2(\''+sheet+'\',this.value)">'
    +'<button class="export-btn" onclick="gExport(\''+sheet+'\')">&#8595; Export CSV</button>'
    +'</div>'
    +stats+tbl+pg;
}

// Alias for onclick (sheet id vs sheet name)
function gNavigate(sid, sheet, dir){ /* patched below */ }

/* ===== INIT ===== */
// Fix gNavigate to accept both sid and sheet
window.gNavigate = function(sheet, dir){
  const view=gView[sheet];let ref=new Date(gDate[sheet]||new Date());
  if(view==='month')ref=new Date(ref.getFullYear(),ref.getMonth()+dir,1);
  else if(view==='week')ref=new Date(ref.getTime()+dir*7*86400000);
  else ref=new Date(ref.getTime()+dir*86400000);
  gDate[sheet]=ref;gOffset[sheet]=0;renderGeneral(sheet);
};

// ── Tab definitions (id, label, group) ─────────────────────────────────────
const TAB_DEFS = [
  {id:'crmtask',       label:'CRM Tasks',        group:'Dashboards'},
  {id:'billing',       label:'Billing',          group:'Dashboards'},
  {id:'census',        label:'Census',           group:'Dashboards'},
  {id:'marketing',     label:'Marketing',        group:'Dashboards'},
  {id:'opportunities', label:'Opportunities',    group:'Dashboards'},
  {id:'referral',      label:'Referrals',        group:'Dashboards'},
  {id:'ur',            label:'UR',               group:'Dashboards'},
  {id:'clinical',      label:'Clinical',         group:'Dashboards'},
  {id:'operations',    label:'Operations',       group:'Dashboards'},
  {id:'fieldexplorer', label:'Field Explorer',   group:'Tools'},
];

// User-controlled tab visibility (persisted in localStorage)
function loadTabVis(){
  try { const c=JSON.parse(localStorage.getItem('sunwave_tab_visibility')||'{}'); return c; } catch(_){ return {}; }
}
function saveTabVis(v){ try { localStorage.setItem('sunwave_tab_visibility', JSON.stringify(v)); } catch(_){} }
let tabVis = loadTabVis();
function isTabVisible(id){ return tabVis[id] !== false; }

// Build the top tab bar
(function buildTabs(){
  const bar=document.getElementById('tabBar');
  if(!bar) return;
  bar.innerHTML='';
  TAB_DEFS.forEach((t,i)=>{
    const b=document.createElement('button');
    b.className='tab-btn'+(i===0?' active':'')+(isTabVisible(t.id)?'':' tab-hidden');
    b.id='btn-'+t.id;
    b.textContent=t.label;
    b.title=t.label;
    b.onclick=()=>showPage(t.id);
    bar.appendChild(b);
  });
  // General report sheets follow as additional tabs (also toggleable)
  SHEETS.forEach(s=>{
    const id=s;
    const b=document.createElement('button');
    b.className='tab-btn'+(isTabVisible(id)?'':' tab-hidden');
    b.id='btn-'+s.replace(/[^a-zA-Z0-9]/g,'_');
    b.textContent=s; b.title=s;
    b.onclick=()=>showPage(s);
    bar.appendChild(b);
  });
})();

// Build the tab visibility menu (gear button)
(function buildTabsMenu(){
  const m=document.getElementById('tabsMenu');
  if(!m) return;
  let h='<div class="tabs-menu-header">Show / Hide Tabs</div>';
  // Dashboards
  h+='<div class="tabs-menu-header" style="border:none;padding-top:6px">Dashboards</div>';
  TAB_DEFS.forEach(t=>{
    h+='<label><input type="checkbox" data-tab="'+t.id+'" '+(isTabVisible(t.id)?'checked':'')+'> '+esc(t.label)+'</label>';
  });
  // Reports
  h+='<div class="tabs-menu-header" style="border:none;padding-top:6px">Report Tabs</div>';
  SHEETS.forEach(s=>{
    h+='<label><input type="checkbox" data-tab="'+esc(s)+'" '+(isTabVisible(s)?'checked':'')+'> '+esc(s)+'</label>';
  });
  h+='<div class="actions"><button onclick="setAllTabsVisible(true)">Show all</button><button onclick="setAllTabsVisible(false)">Hide all</button></div>';
  m.innerHTML=h;
  m.querySelectorAll('input[type=checkbox]').forEach(cb=>{
    cb.onchange=()=>{
      const id=cb.getAttribute('data-tab');
      tabVis[id]=cb.checked;
      saveTabVis(tabVis);
      applyTabVisibility();
    };
  });
})();
function setAllTabsVisible(v){
  TAB_DEFS.forEach(t=>tabVis[t.id]=v);
  SHEETS.forEach(s=>tabVis[s]=v);
  saveTabVis(tabVis);
  // Refresh checkboxes
  document.querySelectorAll('#tabsMenu input[type=checkbox]').forEach(cb=>cb.checked=v);
  applyTabVisibility();
}
function applyTabVisibility(){
  document.querySelectorAll('#tabBar .tab-btn').forEach(b=>{
    const id=b.id.replace(/^btn-/,'');
    // Map ID back to original tab id (might be sanitized for sheets)
    const def = TAB_DEFS.find(t=>t.id===id);
    let realId = def ? def.id : null;
    if(!realId){
      // Sheet name (sanitized)
      realId = SHEETS.find(s=>s.replace(/[^a-zA-Z0-9]/g,'_')===id) || id;
    }
    if(isTabVisible(realId)) b.classList.remove('tab-hidden');
    else b.classList.add('tab-hidden');
  });
}
function toggleTabsMenu(e){
  if(e) e.stopPropagation();
  document.getElementById('tabsMenu').classList.toggle('open');
}
document.addEventListener('click', e => {
  const m=document.getElementById('tabsMenu');
  if(!m) return;
  if(!m.contains(e.target) && !e.target.closest('.topbar-action')){
    m.classList.remove('open');
  }
});

// ── Filter rail population ────────────────────────────────────────────────
function populateFilterRail(pageId, sec){
  const rail=document.getElementById('filterContent');
  if(!rail || !sec) return;
  rail.innerHTML='';
  // Find the section's primary controls bar (first .controls inside the section)
  const ctrls = sec.querySelector('.controls');
  if(ctrls){
    const wrap=document.createElement('div');
    wrap.className='filter-section active';
    wrap.appendChild(ctrls.cloneNode(true));
    // Hide the original to avoid duplication; keep its functionality via the clone
    ctrls.style.display='none';
    rail.appendChild(wrap);
    // Re-bind oninput/onchange handlers in the clone (cloneNode preserves attribute handlers in HTML, but inline event attributes carry over)
  } else {
    rail.innerHTML='<div style="font-size:11.5px;color:#9ca3af;font-style:italic">No filters available for this view.</div>';
  }
}

// ── Excel export (SheetJS) ────────────────────────────────────────────────
function exportPageToExcel(){
  if(typeof XLSX === 'undefined') { alert('Excel library not loaded yet.'); return; }
  const sec = document.querySelector('.page-section[style*="block"], .page-section:not([style*="none"])');
  const active = document.querySelector('.page-section[style="display: block"], .page-section[style*="display:block"]');
  const target = active || sec;
  if(!target){ alert('Nothing to export.'); return; }
  const wb = XLSX.utils.book_new();
  const tables = target.querySelectorAll('table');
  if(!tables.length){ alert('No tables on this page to export.'); return; }
  let sheetIdx=1;
  tables.forEach(t=>{
    try {
      const ws = XLSX.utils.table_to_sheet(t);
      const name = ('Sheet'+(sheetIdx++)).slice(0,31);
      XLSX.utils.book_append_sheet(wb, ws, name);
    } catch(e){ console.warn('Skip table:', e); }
  });
  const fname = 'Sunwave_'+(curPage||'export').replace(/[^a-zA-Z0-9]/g,'_')+'_'+new Date().toISOString().slice(0,10)+'.xlsx';
  XLSX.writeFile(wb, fname);
}

// ── PNG export (html2canvas) ──────────────────────────────────────────────
function exportPageToPNG(){
  if(typeof html2canvas === 'undefined') { alert('Image library not loaded yet.'); return; }
  const target = document.querySelector('.page-section[style*="block"], .page-section:not([style*="none"])');
  if(!target){ alert('Nothing to export.'); return; }
  const btn = document.querySelector('.page-action-btn.blue');
  const orig = btn ? btn.innerHTML : '';
  if(btn) btn.innerHTML='Capturing...';
  html2canvas(target, { backgroundColor:'#f3f5f9', scale: 1.5, useCORS: true }).then(canvas=>{
    canvas.toBlob(blob=>{
      const a=document.createElement('a');
      a.href=URL.createObjectURL(blob);
      a.download='Sunwave_'+(curPage||'export').replace(/[^a-zA-Z0-9]/g,'_')+'_'+new Date().toISOString().slice(0,10)+'.png';
      a.click();
      if(btn) btn.innerHTML=orig;
    });
  }).catch(e=>{
    console.error(e); alert('PNG export failed: '+e.message);
    if(btn) btn.innerHTML=orig;
  });
}

// Build section containers
(function buildSections(){
  const wrap=document.getElementById('sectionsWrap');
  // General report panels
  SHEETS.forEach(s=>{
    const sid=s.replace(/[^a-zA-Z0-9]/g,'_');
    const sec=document.createElement('div');sec.className='page-section';sec.id='sec-'+sid;sec.style.display='none';
    const panel=document.createElement('div');panel.id='gpanel-'+sid;
    sec.appendChild(panel);wrap.appendChild(sec);
  });
})();

// Init general reports date
SHEETS.forEach(s=>{
  const dIdx=DATE_IDX[s];
  if(dIdx>=0)for(const row of RAW[s].rows){const d=pd(row[dIdx]);if(d){gDate[s]=d;break;}}
  if(!gDate[s])gDate[s]=new Date();
});

/* ═══════════════════════════════════════════════════════════════
   CENSUS LOGIC
═══════════════════════════════════════════════════════════════ */
let CROWS = JSON.parse(document.getElementById('censusData').textContent);

// Active census: patients who were active on date D
function cActive(rows, D) {
  return rows.filter(r => {
    const adm = pd(r.adm); if (!adm || adm > D) return false;
    const dis = pd(r.dis); return !dis || dis > D;
  });
}
// Admits in [from, to]
function cAdmits(rows, from, to) { return rows.filter(r => { const d=pd(r.adm); return d&&d>=from&&d<=to; }); }
// Discharges in [from, to]
function cDischarges(rows, from, to) { return rows.filter(r => { const d=pd(r.dis); return d&&d>=from&&d<=to; }); }

// LOC grouping order
const LOC_ORDER = ['Res 3.5','Res 3.1','PHP','Detox','IOP','Other'];
function allLOCs(rows) {
  const s=new Set(rows.map(r=>r.loc||'Other'));
  return LOC_ORDER.filter(l=>s.has(l)).concat([...s].filter(l=>!LOC_ORDER.includes(l)));
}

const CSPOT_PERIODS = [
  { label:'Today',        snap:()=>new Date(TODAY), from:()=>new Date(TODAY),        to:()=>new Date(TODAY) },
  { label:'Yesterday',    snap:()=>daysAgo(1),       from:()=>daysAgo(1),             to:()=>daysAgo(1) },
  { label:'Last 7 Days',  snap:()=>daysAgo(6),       from:()=>daysAgo(6),             to:()=>new Date(TODAY) },
  { label:'Last 31 Days', snap:()=>daysAgo(30),      from:()=>daysAgo(30),            to:()=>new Date(TODAY) },
  { label:'Last 12 Mo',   snap:()=>daysAgo(364),     from:()=>daysAgo(364),           to:()=>new Date(TODAY) },
  { label:'YTD',          snap:()=>new Date(TODAY.getFullYear(),0,1), from:()=>new Date(TODAY.getFullYear(),0,1), to:()=>new Date(TODAY) },
];

function renderCensusSpot() {
  const locs = allLOCs(CROWS);
  let h = '<table class="spot-table"><thead><tr><th>Metric / LOC</th>';
  CSPOT_PERIODS.forEach(p=>h+='<th>'+p.label+'</th>'); h+='</tr></thead><tbody>';

  // Section: ACTIVE CENSUS
  h+='<tr><td colspan="'+(CSPOT_PERIODS.length+1)+'" class="spot-section">ACTIVE CENSUS (as of period end)</td></tr>';
  locs.forEach(loc=>{
    h+='<tr><td class="metric-name">&nbsp;&nbsp;'+esc(loc)+'</td>';
    CSPOT_PERIODS.forEach(p=>{ const n=cActive(CROWS,p.snap()).filter(r=>r.loc===loc).length; h+='<td class="num">'+n+'</td>'; });
    h+='</tr>';
  });
  h+='<tr class="total-row"><td class="metric-name">&nbsp;&nbsp;Total</td>';
  CSPOT_PERIODS.forEach(p=>{ h+='<td class="num">'+cActive(CROWS,p.snap()).length+'</td>'; }); h+='</tr>';

  // Section: ADMITS
  h+='<tr><td colspan="'+(CSPOT_PERIODS.length+1)+'" class="spot-section">ADMITS (in period)</td></tr>';
  locs.forEach(loc=>{
    h+='<tr><td class="metric-name">&nbsp;&nbsp;'+esc(loc)+'</td>';
    CSPOT_PERIODS.forEach(p=>{ h+='<td class="num">'+cAdmits(CROWS,p.from(),p.to()).filter(r=>r.loc===loc).length+'</td>'; });
    h+='</tr>';
  });
  h+='<tr class="total-row"><td class="metric-name">&nbsp;&nbsp;Total</td>';
  CSPOT_PERIODS.forEach(p=>{ h+='<td class="num">'+cAdmits(CROWS,p.from(),p.to()).length+'</td>'; }); h+='</tr>';

  // Section: DISCHARGES
  h+='<tr><td colspan="'+(CSPOT_PERIODS.length+1)+'" class="spot-section">DISCHARGES (in period)</td></tr>';
  locs.forEach(loc=>{
    h+='<tr><td class="metric-name">&nbsp;&nbsp;'+esc(loc)+'</td>';
    CSPOT_PERIODS.forEach(p=>{ h+='<td class="num">'+cDischarges(CROWS,p.from(),p.to()).filter(r=>r.loc===loc).length+'</td>'; });
    h+='</tr>';
  });
  h+='<tr class="total-row"><td class="metric-name">&nbsp;&nbsp;Total</td>';
  CSPOT_PERIODS.forEach(p=>{ h+='<td class="num">'+cDischarges(CROWS,p.from(),p.to()).length+'</td>'; }); h+='</tr>';

  h+='</tbody></table>';
  document.getElementById('cSpotTable').innerHTML=h;

  // Discharge type breakdown
  let h2='<table class="spot-table"><thead><tr><th>Discharge Type</th>';
  CSPOT_PERIODS.forEach(p=>h2+='<th>'+p.label+'</th>'); h2+='</tr></thead><tbody>';
  const dtypes=['Successful','AMA/ASA','Administrative','Transferred'];
  dtypes.forEach(dt=>{
    h2+='<tr><td class="metric-name">'+esc(dt)+'</td>';
    CSPOT_PERIODS.forEach(p=>{
      const dis=cDischarges(CROWS,p.from(),p.to());
      const cnt=dis.filter(r=>r.dtype.startsWith(dt)).length;
      const pct=dis.length>0?(cnt/dis.length*100).toFixed(1)+'%':'0%';
      h2+='<td class="num">'+pct+'</td>';
    });
    h2+='</tr>';
  });
  h2+='<tr class="total-row"><td class="metric-name">Total (count)</td>';
  CSPOT_PERIODS.forEach(p=>h2+='<td class="num">'+cDischarges(CROWS,p.from(),p.to()).length+'</td>');
  h2+='</tr></tbody></table>';
  document.getElementById('cDischargeBreakdown').innerHTML=h2;
}

// ── Monthly trend ──────────────────────────────────────────────────────────
function renderCensusTrend() {
  const months=[];
  for(let i=5;i>=0;i--){const d=new Date(TODAY.getFullYear(),TODAY.getMonth()-i,1);months.push({label:d.toLocaleString('default',{month:'short',year:'2-digit'}),start:d,end:eom(d)});}
  const locs=allLOCs(CROWS);
  const sections=[
    { title:'ACTIVE CENSUS (end of month)', fn:(m,loc)=>cActive(CROWS,m.end).filter(r=>r.loc===loc).length, total:(m)=>cActive(CROWS,m.end).length },
    { title:'ADMITS', fn:(m,loc)=>cAdmits(CROWS,m.start,m.end).filter(r=>r.loc===loc).length, total:(m)=>cAdmits(CROWS,m.start,m.end).length },
    { title:'DISCHARGES', fn:(m,loc)=>cDischarges(CROWS,m.start,m.end).filter(r=>r.loc===loc).length, total:(m)=>cDischarges(CROWS,m.start,m.end).length },
    { title:'NET GROWTH (Admits \u2013 Discharges)', fn:(m,loc)=>cAdmits(CROWS,m.start,m.end).filter(r=>r.loc===loc).length-cDischarges(CROWS,m.start,m.end).filter(r=>r.loc===loc).length, total:(m)=>cAdmits(CROWS,m.start,m.end).length-cDischarges(CROWS,m.start,m.end).length },
  ];
  let h='<table class="trend-table"><thead><tr><th>Metric / LOC</th>';
  months.forEach(m=>h+='<th>'+m.label+'</th>'); h+='</tr></thead><tbody>';
  sections.forEach(sec=>{
    h+='<tr><td colspan="'+(months.length+1)+'" class="spot-section">'+sec.title+'</td></tr>';
    locs.forEach(loc=>{
      h+='<tr><td class="metric-name">&nbsp;&nbsp;'+esc(loc)+'</td>';
      months.forEach(m=>{const v=sec.fn(m,loc);h+='<td class="num">'+(v>0?v:v<0?'<span style="color:#c00">'+v+'</span>':0)+'</td>';});
      h+='</tr>';
    });
    h+='<tr class="total-row"><td class="metric-name">&nbsp;&nbsp;Total</td>';
    months.forEach(m=>{const v=sec.total(m);h+='<td class="num">'+(v>0?v:v<0?'<span style="color:#c00">'+v+'</span>':0)+'</td>';});
    h+='</tr>';
  });
  h+='</tbody></table>';
  document.getElementById('cTrendTable').innerHTML=h;
}

// ── Period nav state for breakdowns ───────────────────────────────────────
let cNavView='all', cNavDate=null;
for(const r of CROWS){const d=pd(r.adm);if(d){cNavDate=d;break;}}
if(!cNavDate)cNavDate=new Date();

function cNavRange(){
  if(cNavView==='all')  return{from:new Date(1900,0,1),to:new Date(2100,0,1)};
  if(cNavView==='year') return{from:new Date(cNavDate.getFullYear(),0,1),to:new Date(cNavDate.getFullYear(),11,31)};
  if(cNavView==='month')return{from:som(cNavDate),to:eom(cNavDate)};
  if(cNavView==='week'){const ws=gwk(cNavDate),we=new Date(ws);we.setDate(we.getDate()+6);return{from:ws,to:we};}
  return{from:new Date(cNavDate),to:new Date(cNavDate)};
}
function cNavLabel(){
  if(cNavView==='all')  return 'All Time';
  if(cNavView==='year') return String(cNavDate.getFullYear());
  if(cNavView==='month')return cNavDate.toLocaleString('default',{month:'long'})+' '+cNavDate.getFullYear();
  if(cNavView==='week'){const{from,to}=cNavRange();return fd(from)+' \u2013 '+fd(to);}
  return fd(cNavDate);
}
function cNavigate(dir){
  if(cNavView==='all') return;
  if(cNavView==='year') cNavDate=new Date(cNavDate.getFullYear()+dir,0,1);
  else if(cNavView==='month')cNavDate=new Date(cNavDate.getFullYear(),cNavDate.getMonth()+dir,1);
  else if(cNavView==='week')cNavDate=new Date(cNavDate.getTime()+dir*7*86400000);
  else cNavDate=new Date(cNavDate.getTime()+dir*86400000);
  renderCensusBreakdowns();
}
function cSetView(v){cNavView=v;renderCensusBreakdowns();}
function cJump(val){if(!val)return;const p=val.split('-');cNavDate=new Date(+p[0],+p[1]-1,+p[2]);renderCensusBreakdowns();}

function pctRow(label,cnt,total){
  const pct=total>0?(cnt/total*100).toFixed(1)+'%':'0%';
  return '<tr><td>'+esc(label)+'</td><td class="num">'+cnt+'</td><td class="num">'+pct+'</td></tr>';
}

function renderCensusBreakdowns(){
  document.getElementById('cPeriodLabel').innerHTML=cNavLabel();
  document.getElementById('cViewMonth').className='view-btn'+(cNavView==='month'?' active':'');
  document.getElementById('cViewWeek').className='view-btn'+(cNavView==='week'?' active':'');
  document.getElementById('cViewDay').className='view-btn'+(cNavView==='day'?' active':'');
  document.getElementById('cViewYear').className='view-btn'+(cNavView==='year'?' active':'');
  document.getElementById('cViewAll').className='view-btn'+(cNavView==='all'?' active':'');

  const{from,to}=cNavRange();
  const admits=cAdmits(CROWS,from,to);
  const discharges=cDischarges(CROWS,from,to);

  // KPI cards
  const snapDate=to;
  const activeNow=cActive(CROWS,snapDate);
  document.getElementById('cKpiActive').textContent=activeNow.length;
  document.getElementById('cKpiAdmits').textContent=admits.length;
  document.getElementById('cKpiDischarges').textContent=discharges.length;
  document.getElementById('cKpiNet').textContent=(admits.length-discharges.length>=0?'+':'')+(admits.length-discharges.length);
  const los=admits.filter(r=>r.los!==null).map(r=>r.los);
  document.getElementById('cKpiLOS').textContent=los.length>0?(los.reduce((s,v)=>s+v,0)/los.length).toFixed(1)+' days':'N/A';

  // Gender
  const genF=admits.filter(r=>r.gen==='F').length, genM=admits.filter(r=>r.gen==='M').length;
  const gTotal=admits.filter(r=>r.gen).length;
  let hg='<table class="break-table"><thead><tr><th>Gender</th><th># Admits</th><th>%</th></tr></thead><tbody>';
  hg+=pctRow('Female',genF,gTotal)+pctRow('Male',genM,gTotal);
  hg+='<tr class="total-row"><td>Total</td><td class="num">'+gTotal+'</td><td class="num">100%</td></tr></tbody></table>';
  document.getElementById('cGenderTable').innerHTML=hg;

  // Age buckets
  const ageBuckets=[['18-24',18,24],['25-34',25,34],['35-44',35,44],['45-54',45,54],['55-64',55,64],['65+',65,999]];
  const aTotal=admits.filter(r=>r.age!==null).length;
  let ha='<table class="break-table"><thead><tr><th>Age Bucket</th><th># Admits</th><th>%</th></tr></thead><tbody>';
  ageBuckets.forEach(([lbl,lo,hi])=>{
    const cnt=admits.filter(r=>r.age!==null&&r.age>=lo&&r.age<=hi).length;
    ha+=pctRow(lbl,cnt,aTotal);
  });
  ha+='<tr class="total-row"><td>Total</td><td class="num">'+aTotal+'</td><td class="num">100%</td></tr></tbody></table>';
  document.getElementById('cAgeTable').innerHTML=ha;

  // Drug of choice
  const drugs=['Alcohol','Stimulant','Opioid','Other'];
  const dAdmits=admits.filter(r=>r.drug);
  let hd='<table class="break-table"><thead><tr><th>Primary Drug</th><th># Admits</th><th>%</th></tr></thead><tbody>';
  drugs.forEach(drg=>{
    const cnt=dAdmits.filter(r=>r.drug===drg).length;
    hd+=pctRow(drg,cnt,dAdmits.length);
  });
  const otherDrugs=dAdmits.filter(r=>!drugs.includes(r.drug)).length;
  if(otherDrugs>0)hd+=pctRow('Other (unlisted)',otherDrugs,dAdmits.length);
  hd+='<tr class="total-row"><td>Total</td><td class="num">'+dAdmits.length+'</td><td class="num">100%</td></tr></tbody></table>';
  document.getElementById('cDrugTable').innerHTML=hd;

  // Discharge type
  const dtypes=['Successful','AMA/ASA','Administrative','Transferred'];
  let hdt='<table class="break-table"><thead><tr><th>Discharge Type</th><th># Discharges</th><th>%</th></tr></thead><tbody>';
  dtypes.forEach(dt=>{
    const cnt=discharges.filter(r=>r.dtype.startsWith(dt)).length;
    hdt+=pctRow(dt,cnt,discharges.length);
  });
  hdt+='<tr class="total-row"><td>Total</td><td class="num">'+discharges.length+'</td><td class="num">100%</td></tr></tbody></table>';
  document.getElementById('cDtypeTable').innerHTML=hdt;

  // Referral sources
  const refMap={};
  admits.forEach(r=>{if(r.ref)refMap[r.ref]=(refMap[r.ref]||0)+1;});
  const refSorted=Object.entries(refMap).sort((a,b)=>b[1]-a[1]);
  const top10=refSorted.slice(0,10), others=refSorted.slice(10).reduce((s,[,v])=>s+v,0);
  let hr='<table class="break-table"><thead><tr><th>Referral Source</th><th># Admits</th><th>%</th></tr></thead><tbody>';
  top10.forEach(([k,v])=>hr+=pctRow(k,v,admits.length));
  if(others>0)hr+=pctRow('Others',others,admits.length);
  hr+='<tr class="total-row"><td>Total</td><td class="num">'+admits.length+'</td><td class="num">100%</td></tr></tbody></table>';
  document.getElementById('cReferralTable').innerHTML=hr;

  // LOS table
  const locs2=allLOCs(CROWS);
  const cohort=CROWS.filter(r=>r.los!==null&&r.dis);
  let hl='<table class="break-table"><thead><tr><th>Level of Care</th><th>Avg LOS (days)</th><th># Patients</th></tr></thead><tbody>';
  locs2.forEach(loc=>{
    const pts=cohort.filter(r=>r.loc===loc);
    const avg=pts.length>0?(pts.reduce((s,r)=>s+r.los,0)/pts.length).toFixed(1):'-';
    hl+='<tr><td>'+esc(loc)+'</td><td class="num">'+avg+'</td><td class="num">'+pts.length+'</td></tr>';
  });
  const allAvg=cohort.length>0?(cohort.reduce((s,r)=>s+r.los,0)/cohort.length).toFixed(1):'-';
  hl+='<tr class="total-row"><td>All LOC (overall)</td><td class="num">'+allAvg+'</td><td class="num">'+cohort.length+'</td></tr>';
  hl+='</tbody></table>';
  document.getElementById('cLOSTable').innerHTML=hl;
}

/* ═══════════════════════════════════════════════════════════════
   MARKETING LOGIC
═══════════════════════════════════════════════════════════════ */
let OROWS = JSON.parse(document.getElementById('oppData').textContent);

function mFilter(rows,from,to){return rows.filter(r=>{const d=pd(r.co);return d&&d>=from&&d<=to;});}
function mMetrics(rows){
  const total=rows.length;
  const admitted=rows.filter(r=>r.outcome==='Admitted'||r.outcome==='AdmittedLegacy').length;
  const active=rows.filter(r=>r.outcome==='Active').length;
  const scheduled=rows.filter(r=>r.outcome==='Scheduled').length;
  const lost=rows.filter(r=>r.outcome==='Lost').length;
  const abandoned=rows.filter(r=>r.outcome==='Abandoned').length;
  return{total,admitted,active,scheduled,lost,abandoned,rate:total>0?admitted/total:0};
}
const MKT_PERIODS=[
  {label:'Today',from:()=>new Date(TODAY),to:()=>new Date(TODAY)},
  {label:'Yesterday',from:()=>daysAgo(1),to:()=>daysAgo(1)},
  {label:'Last 7 Days',from:()=>daysAgo(6),to:()=>new Date(TODAY)},
  {label:'Last 31 Days',from:()=>daysAgo(30),to:()=>new Date(TODAY)},
  {label:'Last 90 Days',from:()=>daysAgo(89),to:()=>new Date(TODAY)},
  {label:'Last 12 Mo',from:()=>daysAgo(364),to:()=>new Date(TODAY)},
  {label:'YTD',from:()=>new Date(TODAY.getFullYear(),0,1),to:()=>new Date(TODAY)},
];
const MKT_METRICS=[
  {key:'total',label:'Total Created',fmt:v=>v.toLocaleString()},
  {key:'active',label:'Active',fmt:v=>v.toLocaleString()},
  {key:'scheduled',label:'Scheduled',fmt:v=>v.toLocaleString()},
  {key:'admitted',label:'Admitted',fmt:v=>v.toLocaleString()},
  {key:'lost',label:'Lost',fmt:v=>v.toLocaleString()},
  {key:'abandoned',label:'Abandoned',fmt:v=>v.toLocaleString()},
  {key:'rate',label:'Admit Rate',fmt:v=>fmtPct(v)},
];

function renderMarketingSpot(){
  let h='<table class="spot-table"><thead><tr><th>Metric</th>';
  MKT_PERIODS.forEach(p=>h+='<th>'+p.label+'</th>'); h+='</tr></thead><tbody>';
  MKT_METRICS.forEach(m=>{
    h+='<tr><td class="metric-name">'+m.label+'</td>';
    MKT_PERIODS.forEach(p=>{const c=mMetrics(mFilter(OROWS,p.from(),p.to()));h+='<td class="num">'+m.fmt(c[m.key])+'</td>';});
    h+='</tr>';
  });
  h+='</tbody></table>';
  document.getElementById('mktSpot').innerHTML=h;
}

let mktNavView='all',mktNavDate=null;
for(const r of OROWS){const d=pd(r.co);if(d){mktNavDate=d;break;}}
if(!mktNavDate)mktNavDate=new Date();

function mktNavRange(){
  if(mktNavView==='all')  return{from:new Date(1900,0,1),to:new Date(2100,0,1)};
  if(mktNavView==='year') return{from:new Date(mktNavDate.getFullYear(),0,1),to:new Date(mktNavDate.getFullYear(),11,31)};
  if(mktNavView==='month')return{from:som(mktNavDate),to:eom(mktNavDate)};
  if(mktNavView==='week'){const ws=gwk(mktNavDate),we=new Date(ws);we.setDate(we.getDate()+6);return{from:ws,to:we};}
  return{from:new Date(mktNavDate),to:new Date(mktNavDate)};
}
function mktNavLabel(){
  if(mktNavView==='all')  return 'All Time';
  if(mktNavView==='year') return String(mktNavDate.getFullYear());
  if(mktNavView==='month')return mktNavDate.toLocaleString('default',{month:'long'})+' '+mktNavDate.getFullYear();
  if(mktNavView==='week'){const{from,to}=mktNavRange();return fd(from)+' \u2013 '+fd(to);}
  return fd(mktNavDate);
}
function mktNavigate(dir){
  if(mktNavView==='all') return;
  if(mktNavView==='year') mktNavDate=new Date(mktNavDate.getFullYear()+dir,0,1);
  else if(mktNavView==='month')mktNavDate=new Date(mktNavDate.getFullYear(),mktNavDate.getMonth()+dir,1);
  else if(mktNavView==='week')mktNavDate=new Date(mktNavDate.getTime()+dir*7*86400000);
  else mktNavDate=new Date(mktNavDate.getTime()+dir*86400000);
  renderMarketingDetail();
}
function mktSetView(v){mktNavView=v;renderMarketingDetail();}
function mktJump(val){if(!val)return;const p=val.split('-');mktNavDate=new Date(+p[0],+p[1]-1,+p[2]);renderMarketingDetail();}

function renderMarketingTrend(){
  const months=[];for(let i=5;i>=0;i--){const d=new Date(TODAY.getFullYear(),TODAY.getMonth()-i,1);months.push({label:d.toLocaleString('default',{month:'short',year:'2-digit'}),from:d,to:eom(d)});}
  let h='<table class="trend-table"><thead><tr><th>Metric</th>';
  months.forEach(m=>h+='<th>'+m.label+'</th>'); h+='</tr></thead><tbody>';
  MKT_METRICS.forEach(m=>{
    h+='<tr><td class="metric-name">'+m.label+'</td>';
    months.forEach(mo=>{const c=mMetrics(mFilter(OROWS,mo.from,mo.to));h+='<td class="num">'+m.fmt(c[m.key])+'</td>';});
    h+='</tr>';
  });
  h+='</tbody></table>';
  document.getElementById('mktTrend').innerHTML=h;
}

function renderMarketingDetail(){
  document.getElementById('mktPeriodLabel').innerHTML=mktNavLabel();
  document.getElementById('mktViewMonth').className='view-btn'+(mktNavView==='month'?' active':'');
  document.getElementById('mktViewWeek').className='view-btn'+(mktNavView==='week'?' active':'');
  document.getElementById('mktViewDay').className='view-btn'+(mktNavView==='day'?' active':'');
  document.getElementById('mktViewYear').className='view-btn'+(mktNavView==='year'?' active':'');
  document.getElementById('mktViewAll').className='view-btn'+(mktNavView==='all'?' active':'');
  const{from,to}=mktNavRange();
  const rows=mFilter(OROWS,from,to);
  const m=mMetrics(rows);
  document.getElementById('mktKpiTotal').textContent=m.total;
  document.getElementById('mktKpiAdmitted').textContent=m.admitted;
  document.getElementById('mktKpiRate').textContent=fmtPct(m.rate);
  document.getElementById('mktKpiActive').textContent=m.active;
  document.getElementById('mktKpiLost').textContent=m.lost;
  document.getElementById('mktKpiAbandoned').textContent=m.abandoned;

  // Funnel
  const funnelItems=[
    {label:'Created',val:m.total,color:'#1a3a5c'},
    {label:'Active',val:m.active,color:'#1a6ec0'},
    {label:'Scheduled',val:m.scheduled,color:'#2196f3'},
    {label:'Admitted',val:m.admitted,color:'#217346'},
    {label:'Lost',val:m.lost,color:'#c86a00'},
    {label:'Abandoned',val:m.abandoned,color:'#888'},
  ];
  const maxV=m.total||1;
  let hf='';
  funnelItems.forEach(f=>{
    const pct=Math.round(f.val/maxV*100);
    const dark=pct<15;
    hf+='<div class="funnel-bar"><span class="funnel-label">'+f.label+'</span>'
      +'<div class="funnel-track"><div class="funnel-fill" style="width:'+pct+'%;background:'+f.color+'"></div>'
      +'<span class="funnel-val'+(dark?' dark':'')+'">'+f.val+' ('+fmtPct(m.total>0?f.val/m.total:0)+')</span></div></div>';
  });
  document.getElementById('mktFunnel').innerHTML=hf;

  // Lost reasons
  const lostRows=OROWS.filter(r=>r.outcome==='Lost'&&r.lost_r);
  const lostMap={};lostRows.forEach(r=>lostMap[r.lost_r]=(lostMap[r.lost_r]||0)+1);
  let hl='<table class="break-table"><thead><tr><th>Reason</th><th>#</th><th>%</th></tr></thead><tbody>';
  Object.entries(lostMap).sort((a,b)=>b[1]-a[1]).forEach(([k,v])=>hl+='<tr><td>'+esc(k)+'</td><td class="num">'+v+'</td><td class="num">'+(lostRows.length>0?(v/lostRows.length*100).toFixed(1)+'%':'0%')+'</td></tr>');
  hl+='<tr class="total-row"><td>Total</td><td class="num">'+lostRows.length+'</td><td class="num">100%</td></tr></tbody></table>';
  document.getElementById('mktLostTable').innerHTML=hl;

  // Abandoned reasons
  const abandRows=OROWS.filter(r=>r.outcome==='Abandoned'&&r.aband_r);
  const abandMap={};abandRows.forEach(r=>abandMap[r.aband_r]=(abandMap[r.aband_r]||0)+1);
  let ha='<table class="break-table"><thead><tr><th>Reason</th><th>#</th><th>%</th></tr></thead><tbody>';
  Object.entries(abandMap).sort((a,b)=>b[1]-a[1]).forEach(([k,v])=>ha+='<tr><td>'+esc(k)+'</td><td class="num">'+v+'</td><td class="num">'+(abandRows.length>0?(v/abandRows.length*100).toFixed(1)+'%':'0%')+'</td></tr>');
  ha+='<tr class="total-row"><td>Total</td><td class="num">'+abandRows.length+'</td><td class="num">100%</td></tr></tbody></table>';
  document.getElementById('mktAbandTable').innerHTML=ha;

  // Top referral sources for admitted
  const admRows=rows.filter(r=>r.outcome==='Admitted'||r.outcome==='AdmittedLegacy');
  const refMap={};admRows.forEach(r=>{if(r.ref)refMap[r.ref]=(refMap[r.ref]||0)+1;});
  const topRef=Object.entries(refMap).sort((a,b)=>b[1]-a[1]).slice(0,10);
  let hr='<table class="break-table"><thead><tr><th>Referral Source</th><th>Admitted</th><th>%</th></tr></thead><tbody>';
  topRef.forEach(([k,v])=>hr+='<tr><td>'+esc(k)+'</td><td class="num">'+v+'</td><td class="num">'+(admRows.length>0?(v/admRows.length*100).toFixed(1)+'%':'0%')+'</td></tr>');
  hr+='<tr class="total-row"><td>Total</td><td class="num">'+admRows.length+'</td><td class="num">100%</td></tr></tbody></table>';
  document.getElementById('mktRefTable').innerHTML=hr;
}

/* ═══════════════════════════════════════════════════════════════
   OPPORTUNITIES DETAIL LOGIC
═══════════════════════════════════════════════════════════════ */
let TLROWS = JSON.parse(document.getElementById('tlData').textContent);
// Index timeline by opportunity_id for fast lookup
const TL_BY_OID = (function(){
  const m={};
  TLROWS.forEach(t=>{ if(!t.oid) return; (m[t.oid]=m[t.oid]||[]).push(t); });
  // Sort each opportunity's timeline newest first
  Object.keys(m).forEach(k=>m[k].sort((a,b)=>(b.sortKey||0)-(a.sortKey||0)));
  return m;
})();
const oppExpanded = new Set(); // tracks expanded opportunity ids
function oppToggle(id){
  if(oppExpanded.has(id)) oppExpanded.delete(id); else oppExpanded.add(id);
  renderOpportunities();
}
function renderTimelineEntries(oid){
  const entries = TL_BY_OID[oid] || [];
  if(!entries.length) return '<div style="padding:14px;color:#999;font-style:italic">No timeline entries for this opportunity.</div>';
  let h='<div style="padding:8px 14px;background:#f5f8fc"><table style="width:100%;border-collapse:collapse;font-size:11.5px">';
  h+='<thead><tr style="background:#1a3a5c;color:#fff"><th style="padding:6px 10px;text-align:left">Date</th><th style="padding:6px 10px;text-align:left">Type</th><th style="padding:6px 10px;text-align:left">Status</th><th style="padding:6px 10px;text-align:left">By</th><th style="padding:6px 10px;text-align:left">Note</th></tr></thead><tbody>';
  entries.forEach(t=>{
    h+='<tr style="border-bottom:1px solid #e0e6ee;background:#fff"><td style="padding:5px 10px;white-space:nowrap;color:#1a3a5c;font-weight:600">'+esc(t.date)+'</td>'
      +'<td style="padding:5px 10px;white-space:nowrap">'+esc(t.type)+'</td>'
      +'<td style="padding:5px 10px;white-space:nowrap">'+esc(t.wf)+'</td>'
      +'<td style="padding:5px 10px;white-space:nowrap">'+esc(t.by)+'</td>'
      +'<td style="padding:5px 10px;white-space:normal;max-width:600px">'+esc(t.text||t.subject)+'</td></tr>';
  });
  h+='</tbody></table></div>';
  return h;
}

let oppNavView='all',oppNavDate=null,oppSearch='',oppSortCol='co',oppSortAsc=false;
for(const r of OROWS){const d=pd(r.co);if(d){oppNavDate=d;break;}}
if(!oppNavDate)oppNavDate=new Date();

function oppNavRange(){
  if(oppNavView==='all')  return{from:new Date(1900,0,1),to:new Date(2100,0,1)};
  if(oppNavView==='year') return{from:new Date(oppNavDate.getFullYear(),0,1),to:new Date(oppNavDate.getFullYear(),11,31)};
  if(oppNavView==='month')return{from:som(oppNavDate),to:eom(oppNavDate)};
  if(oppNavView==='week'){const ws=gwk(oppNavDate),we=new Date(ws);we.setDate(we.getDate()+6);return{from:ws,to:we};}
  return{from:new Date(oppNavDate),to:new Date(oppNavDate)};
}
function oppNavLabel(){
  if(oppNavView==='all')  return 'All Time';
  if(oppNavView==='year') return String(oppNavDate.getFullYear());
  if(oppNavView==='month')return oppNavDate.toLocaleString('default',{month:'long'})+' '+oppNavDate.getFullYear();
  if(oppNavView==='week'){const{from,to}=oppNavRange();return fd(from)+' \u2013 '+fd(to);}
  return fd(oppNavDate);
}
function oppNavigate(dir){
  if(oppNavView==='all') return;
  if(oppNavView==='year') oppNavDate=new Date(oppNavDate.getFullYear()+dir,0,1);
  else if(oppNavView==='month')oppNavDate=new Date(oppNavDate.getFullYear(),oppNavDate.getMonth()+dir,1);
  else if(oppNavView==='week')oppNavDate=new Date(oppNavDate.getTime()+dir*7*86400000);
  else oppNavDate=new Date(oppNavDate.getTime()+dir*86400000);
  renderOpportunities();
}
function oppSetView(v){oppNavView=v;renderOpportunities();}
function oppJump(val){if(!val)return;const p=val.split('-');oppNavDate=new Date(+p[0],+p[1]-1,+p[2]);renderOpportunities();}
function oppSetSort(col){if(oppSortCol===col)oppSortAsc=!oppSortAsc;else{oppSortCol=col;oppSortAsc=false;}renderOpportunities();}

function renderOpportunities(){
  document.getElementById('oppPeriodLabel').innerHTML=oppNavLabel();
  document.getElementById('oppViewMonth').className='view-btn'+(oppNavView==='month'?' active':'');
  document.getElementById('oppViewWeek').className='view-btn'+(oppNavView==='week'?' active':'');
  document.getElementById('oppViewDay').className='view-btn'+(oppNavView==='day'?' active':'');
  document.getElementById('oppViewYear').className='view-btn'+(oppNavView==='year'?' active':'');
  document.getElementById('oppViewAll').className='view-btn'+(oppNavView==='all'?' active':'');
  const{from,to}=oppNavRange();
  let rows=mFilter(OROWS,from,to);
  if(oppSearch){const s=oppSearch.toLowerCase();rows=rows.filter(r=>Object.values(r).some(v=>String(v).toLowerCase().includes(s)));}
  rows=rows.slice().sort((a,b)=>{
    const av=String(a[oppSortCol]||''),bv=String(b[oppSortCol]||'');
    const ad2=pd(av),bd2=pd(bv);if(ad2&&bd2)return oppSortAsc?(ad2-bd2):(bd2-ad2);
    return oppSortAsc?av.localeCompare(bv):bv.localeCompare(av);
  });
  // KPIs
  const m=mMetrics(rows);
  document.getElementById('oppKpiTotal').textContent=m.total;
  document.getElementById('oppKpiAdmitted').textContent=m.admitted;
  document.getElementById('oppKpiRate').textContent=fmtPct(m.rate);
  document.getElementById('oppKpiActive').textContent=m.active;
  // By outcome
  const outcomes=['Active','Scheduled','Admitted','AdmittedLegacy','Lost','Abandoned'];
  const outcomeMap={};rows.forEach(r=>outcomeMap[r.outcome]=(outcomeMap[r.outcome]||0)+1);
  let ho='<table class="break-table"><thead><tr><th>Outcome</th><th>#</th><th>%</th></tr></thead><tbody>';
  Object.entries(outcomeMap).sort((a,b)=>b[1]-a[1]).forEach(([k,v])=>ho+='<tr><td>'+esc(k)+'</td><td class="num">'+v+'</td><td class="num">'+(rows.length>0?(v/rows.length*100).toFixed(1)+'%':'0%')+'</td></tr>');
  ho+='<tr class="total-row"><td>Total</td><td class="num">'+rows.length+'</td><td class="num">100%</td></tr></tbody></table>';
  document.getElementById('oppOutcomeTable').innerHTML=ho;
  // By insurance
  const insMap={};rows.forEach(r=>{if(r.ins)insMap[r.ins]=(insMap[r.ins]||0)+1;});
  let hi='<table class="break-table"><thead><tr><th>Insurance</th><th>#</th><th>%</th></tr></thead><tbody>';
  Object.entries(insMap).sort((a,b)=>b[1]-a[1]).slice(0,10).forEach(([k,v])=>hi+='<tr><td>'+esc(k)+'</td><td class="num">'+v+'</td><td class="num">'+(rows.length>0?(v/rows.length*100).toFixed(1)+'%':'0%')+'</td></tr>');
  hi+='<tr class="total-row"><td>Total</td><td class="num">'+rows.length+'</td><td class="num">100%</td></tr></tbody></table>';
  document.getElementById('oppInsTable').innerHTML=hi;
  // Table with expand/collapse + opportunity ID
  const cols=['id','co','name','outcome','stage','loc','ins','ref'];
  const hdrs=['Opportunity ID','Created On','Patient','Outcome','Stage','LOC','Insurance','Referral'];
  let ht='<div class="table-wrap"><table><thead><tr><th style="width:36px"></th>';
  cols.forEach((c,i)=>{const arr=oppSortCol===c?(oppSortAsc?' &#9650;':' &#9660;'):'';ht+='<th onclick="oppSetSort(\''+c+'\')">'+hdrs[i]+arr+'</th>';});
  ht+='<th style="width:80px">Timeline</th></tr></thead><tbody>';
  const pg=rows.slice(0,150);
  if(!pg.length)ht+='<tr><td colspan="'+(cols.length+2)+'" class="no-data">No records.</td></tr>';
  pg.forEach(r=>{
    const isOpen = oppExpanded.has(r.id);
    const tlCount = (TL_BY_OID[r.id]||[]).length;
    const arrow = isOpen ? '&#9660;' : '&#9658;';
    ht+='<tr style="cursor:pointer" onclick="oppToggle(\''+esc(r.id)+'\')">'
      +'<td style="text-align:center;color:#1a6ec0;font-weight:700">'+arrow+'</td>';
    cols.forEach(c=>{ht+='<td title="'+esc(r[c])+'">'+esc(r[c])+'</td>';});
    ht+='<td style="text-align:center;color:#666;font-size:11px">'+(tlCount>0?'<span style="background:#1a6ec0;color:#fff;padding:2px 8px;border-radius:10px;font-weight:600">'+tlCount+'</span>':'-')+'</td></tr>';
    if(isOpen){
      ht+='<tr class="tl-row"><td colspan="'+(cols.length+2)+'" style="padding:0;background:#f5f8fc">'+renderTimelineEntries(r.id)+'</td></tr>';
    }
  });
  ht+='</tbody></table></div>';
  if(rows.length>150)ht+='<div class="page-info" style="margin-top:6px">Showing 150 of '+rows.length+' records.</div>';
  document.getElementById('oppTableWrap').innerHTML=ht;
}

/* ═══════════════════════════════════════════════════════════════
   REFERRAL ACTIVE LOGIC (with timeline expand/collapse)
═══════════════════════════════════════════════════════════════ */
const RFROWS = JSON.parse(document.getElementById('refData').textContent);
// Build referral timeline lookup (Timeline rows where associated_with == 'Referral')
const REF_TL_BY_ID = (function(){
  const m={};
  TLROWS.forEach(t=>{
    // Treat as referral timeline if oid matches a referral_id, OR associated_with hints 'Referral'
    if(!t.oid) return;
    (m[t.oid]=m[t.oid]||[]).push(t);
  });
  Object.keys(m).forEach(k=>m[k].sort((a,b)=>(b.sortKey||0)-(a.sortKey||0)));
  return m;
})();
const refExpanded = new Set();
function refToggle(id){
  if(refExpanded.has(id)) refExpanded.delete(id); else refExpanded.add(id);
  renderReferrals();
}

let refNavView='all', refNavDate=null, refSearch='';
for(const r of RFROWS){const d=pd(r.co);if(d){refNavDate=d;break;}}
if(!refNavDate) refNavDate=new Date();

function refNavRange(){
  if(refNavView==='all')  return{from:new Date(1900,0,1),to:new Date(2100,0,1)};
  if(refNavView==='year') return{from:new Date(refNavDate.getFullYear(),0,1),to:new Date(refNavDate.getFullYear(),11,31)};
  if(refNavView==='month')return{from:som(refNavDate),to:eom(refNavDate)};
  if(refNavView==='week'){const ws=gwk(refNavDate),we=new Date(ws);we.setDate(we.getDate()+6);return{from:ws,to:we};}
  return{from:new Date(refNavDate),to:new Date(refNavDate)};
}
function refNavLabel(){
  if(refNavView==='all')  return 'All Time';
  if(refNavView==='year') return String(refNavDate.getFullYear());
  if(refNavView==='month')return refNavDate.toLocaleString('default',{month:'long'})+' '+refNavDate.getFullYear();
  if(refNavView==='week'){const{from,to}=refNavRange();return fd(from)+' – '+fd(to);}
  return fd(refNavDate);
}
function refNavigate(dir){
  if(refNavView==='all') return;
  if(refNavView==='year') refNavDate=new Date(refNavDate.getFullYear()+dir,0,1);
  else if(refNavView==='month')refNavDate=new Date(refNavDate.getFullYear(),refNavDate.getMonth()+dir,1);
  else if(refNavView==='week')refNavDate=new Date(refNavDate.getTime()+dir*7*86400000);
  else refNavDate=new Date(refNavDate.getTime()+dir*86400000);
  renderReferrals();
}
function refSetView(v){refNavView=v;renderReferrals();if(curPage==='referral'){const sec=document.getElementById('sec-referral');populateFilterRail('referral',sec);}}
function refJump(val){if(!val)return;const p=val.split('-');refNavDate=new Date(+p[0],+p[1]-1,+p[2]);renderReferrals();}

function renderReferralTimelineEntries(rid){
  const entries = REF_TL_BY_ID[rid] || [];
  if(!entries.length) return '<div style="padding:14px;color:#999;font-style:italic">No timeline entries for this referral.</div>';
  let h='<div style="padding:8px 14px;background:#f5f8fc"><table style="width:100%;border-collapse:collapse;font-size:11.5px">';
  h+='<thead><tr style="background:#1a3a5c;color:#fff"><th style="padding:6px 10px;text-align:left">Date</th><th style="padding:6px 10px;text-align:left">Type</th><th style="padding:6px 10px;text-align:left">Status</th><th style="padding:6px 10px;text-align:left">By</th><th style="padding:6px 10px;text-align:left">Note</th></tr></thead><tbody>';
  entries.forEach(t=>{
    h+='<tr style="border-bottom:1px solid #e0e6ee;background:#fff"><td style="padding:5px 10px;white-space:nowrap;color:#1a3a5c;font-weight:600">'+esc(t.date)+'</td>'
      +'<td style="padding:5px 10px;white-space:nowrap">'+esc(t.type)+'</td>'
      +'<td style="padding:5px 10px;white-space:nowrap">'+esc(t.wf)+'</td>'
      +'<td style="padding:5px 10px;white-space:nowrap">'+esc(t.by)+'</td>'
      +'<td style="padding:5px 10px;white-space:normal;max-width:600px">'+esc(t.text||t.subject)+'</td></tr>';
  });
  h+='</tbody></table></div>';
  return h;
}

function renderReferrals(){
  const lbl=document.getElementById('refPeriodLabel'); if(lbl) lbl.innerHTML=refNavLabel();
  ['Month','Week','Day','Year','All'].forEach(v=>{const e=document.getElementById('refView'+v);if(e)e.className='view-btn'+(refNavView===v.toLowerCase()?' active':'');});
  const{from,to}=refNavRange();
  let rows=RFROWS.filter(r=>{ if(refNavView==='all') return true; const d=pd(r.co); return d&&d>=from&&d<=to; });
  if(refSearch){const s=refSearch.toLowerCase();rows=rows.filter(r=>Object.values(r).some(v=>String(v).toLowerCase().includes(s)));}

  // KPIs
  const totalTL = rows.reduce((s,r)=>s+(REF_TL_BY_ID[r.id]||[]).length,0);
  const types = new Set(rows.map(r=>r.type).filter(Boolean));
  if(document.getElementById('refKpiTotal')) document.getElementById('refKpiTotal').textContent = rows.length;
  if(document.getElementById('refKpiTimeline')) document.getElementById('refKpiTimeline').textContent = totalTL;
  if(document.getElementById('refKpiTypes')) document.getElementById('refKpiTypes').textContent = types.size;

  // By type
  const tMap={}; rows.forEach(r=>{ if(r.type) tMap[r.type]=(tMap[r.type]||0)+1; });
  let ht='<table class="break-table"><thead><tr><th>Type</th><th>#</th><th>%</th></tr></thead><tbody>';
  Object.entries(tMap).sort((a,b)=>b[1]-a[1]).forEach(([k,v])=>ht+='<tr><td>'+esc(k)+'</td><td class="num">'+v+'</td><td class="num">'+(rows.length>0?(v/rows.length*100).toFixed(1)+'%':'0%')+'</td></tr>');
  ht+='<tr class="total-row"><td>Total</td><td class="num">'+rows.length+'</td><td class="num">100%</td></tr></tbody></table>';
  if(document.getElementById('refTypeTable')) document.getElementById('refTypeTable').innerHTML=ht;

  // By owner
  const oMap={}; rows.forEach(r=>{ if(r.owner) oMap[r.owner]=(oMap[r.owner]||0)+1; });
  let ho='<table class="break-table"><thead><tr><th>Owner</th><th>#</th><th>%</th></tr></thead><tbody>';
  Object.entries(oMap).sort((a,b)=>b[1]-a[1]).slice(0,15).forEach(([k,v])=>ho+='<tr><td>'+esc(k)+'</td><td class="num">'+v+'</td><td class="num">'+(rows.length>0?(v/rows.length*100).toFixed(1)+'%':'0%')+'</td></tr>');
  ho+='<tr class="total-row"><td>Total</td><td class="num">'+rows.length+'</td><td class="num">100%</td></tr></tbody></table>';
  if(document.getElementById('refOwnerTable')) document.getElementById('refOwnerTable').innerHTML=ho;

  // Table with expand/collapse + timeline rows
  const cols=['id','co','name','type','stage','owner','city','state'];
  const hdrs=['Referral ID','Created On','Name','Type','Stage','Owner','City','State'];
  let h='<div class="table-wrap"><table><thead><tr><th style="width:36px"></th>';
  cols.forEach((c,i)=>{h+='<th>'+hdrs[i]+'</th>';});
  h+='<th style="width:80px">Timeline</th></tr></thead><tbody>';
  const pg=rows.slice(0,200);
  if(!pg.length) h+='<tr><td colspan="'+(cols.length+2)+'" class="no-data">No referrals.</td></tr>';
  pg.forEach(r=>{
    const isOpen=refExpanded.has(r.id);
    const tlCount=(REF_TL_BY_ID[r.id]||[]).length;
    const arrow=isOpen?'&#9660;':'&#9658;';
    h+='<tr style="cursor:pointer" onclick="refToggle(\''+esc(r.id)+'\')">'
      +'<td style="text-align:center;color:#1a6ec0;font-weight:700">'+arrow+'</td>';
    cols.forEach(c=>{ h+='<td title="'+esc(r[c])+'">'+esc(r[c])+'</td>'; });
    h+='<td style="text-align:center;font-size:11px">'+(tlCount>0?'<span style="background:#1a6ec0;color:#fff;padding:2px 8px;border-radius:10px;font-weight:600">'+tlCount+'</span>':'-')+'</td></tr>';
    if(isOpen){
      h+='<tr class="tl-row"><td colspan="'+(cols.length+2)+'" style="padding:0;background:#f5f8fc">'+renderReferralTimelineEntries(r.id)+'</td></tr>';
    }
  });
  h+='</tbody></table></div>';
  if(rows.length>200) h+='<div class="page-info" style="margin-top:6px">Showing 200 of '+rows.length+' records.</div>';
  if(document.getElementById('refTableWrap')) document.getElementById('refTableWrap').innerHTML=h;
}

/* ═══════════════════════════════════════════════════════════════
   CRM TASK LOGIC
═══════════════════════════════════════════════════════════════ */
let CTROWS = JSON.parse(document.getElementById('crmTaskData').textContent);
let ctNavView='all', ctNavDate=null, ctSearch='', ctStatus='', ctType='', ctAssoc='';
const ctExpanded = new Set();
for(const r of CTROWS){const d=pd(r.activity);if(d){ctNavDate=d;break;}}
if(!ctNavDate) ctNavDate=new Date();

function ctNavRange(){
  if(ctNavView==='all')  return{from:new Date(1900,0,1),to:new Date(2100,0,1)};
  if(ctNavView==='year') return{from:new Date(ctNavDate.getFullYear(),0,1),to:new Date(ctNavDate.getFullYear(),11,31)};
  if(ctNavView==='month')return{from:som(ctNavDate),to:eom(ctNavDate)};
  if(ctNavView==='week'){const ws=gwk(ctNavDate),we=new Date(ws);we.setDate(we.getDate()+6);return{from:ws,to:we};}
  return{from:new Date(ctNavDate),to:new Date(ctNavDate)};
}
function ctNavLabel(){
  if(ctNavView==='all')  return 'All Time';
  if(ctNavView==='year') return String(ctNavDate.getFullYear());
  if(ctNavView==='month')return ctNavDate.toLocaleString('default',{month:'long'})+' '+ctNavDate.getFullYear();
  if(ctNavView==='week'){const{from,to}=ctNavRange();return fd(from)+' – '+fd(to);}
  return fd(ctNavDate);
}
function ctNavigate(dir){
  if(ctNavView==='all') return;
  if(ctNavView==='year') ctNavDate=new Date(ctNavDate.getFullYear()+dir,0,1);
  else if(ctNavView==='month')ctNavDate=new Date(ctNavDate.getFullYear(),ctNavDate.getMonth()+dir,1);
  else if(ctNavView==='week')ctNavDate=new Date(ctNavDate.getTime()+dir*7*86400000);
  else ctNavDate=new Date(ctNavDate.getTime()+dir*86400000);
  renderCRMTask();
}
function ctSetView(v){ctNavView=v;renderCRMTask();if(curPage==='crmtask'){const sec=document.getElementById('sec-crmtask');populateFilterRail('crmtask',sec);}}
function ctJump(val){if(!val)return;const p=val.split('-');ctNavDate=new Date(+p[0],+p[1]-1,+p[2]);renderCRMTask();}
function ctToggle(id){ if(ctExpanded.has(id)) ctExpanded.delete(id); else ctExpanded.add(id); renderCRMTask(); }

function ctParseAct(s){
  if(!s) return null;
  const m = String(s).match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})/);
  if(m){const d=new Date(+m[3],+m[1]-1,+m[2]);d.setHours(0,0,0,0);return d;}
  return pd(s);
}

function ctFiltered(){
  const{from,to}=ctNavRange();
  let rows=CTROWS.filter(r=>{
    if(ctNavView!=='all'){ const d=ctParseAct(r.activity); if(!d) return false; if(d<from||d>to) return false; }
    if(ctStatus && (r.status||'').toLowerCase()!==ctStatus.toLowerCase()) return false;
    if(ctType && (r.task_type||'').toLowerCase()!==ctType.toLowerCase()) return false;
    if(ctAssoc && (r.assoc||'').toLowerCase()!==ctAssoc.toLowerCase()) return false;
    if(ctSearch){const s=ctSearch.toLowerCase();if(!Object.values(r).some(v=>String(v).toLowerCase().includes(s))) return false;}
    return true;
  });
  rows.sort((a,b)=>(b.sortKey||0)-(a.sortKey||0));
  return rows;
}

function ctExport(){
  const rows=ctFiltered();
  const cols=['id','aid','assoc','subject','type','task_type','status','created_by','assigned','activity','due','reminder','text'];
  let csv=cols.map(c=>'"'+c+'"').join(',')+'\n';
  rows.forEach(r=>{csv+=cols.map(c=>'"'+String(r[c]||'').replace(/"/g,'""').replace(/\n/g,' ')+'"').join(',')+'\n';});
  const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv'}));
  a.download='crm_tasks_'+ctNavLabel().replace(/[^a-z0-9]/gi,'_')+'.csv';a.click();
}

function renderCRMTask(){
  // View buttons
  ['Month','Week','Day','Year','All'].forEach(v=>{const e=document.getElementById('ctView'+v);if(e)e.className='view-btn'+(ctNavView===v.toLowerCase()?' active':'');});
  const lbl=document.getElementById('ctPeriodLabel'); if(lbl) lbl.innerHTML=ctNavLabel();
  // Restore filter selects
  const ss=document.getElementById('ctStatusSel'); if(ss) ss.value=ctStatus;
  const ts=document.getElementById('ctTypeSel');   if(ts) ts.value=ctType;
  const as=document.getElementById('ctAssocSel');  if(as) as.value=ctAssoc;

  const rows=ctFiltered();
  const today=new Date(); today.setHours(0,0,0,0);

  // KPIs
  const open = rows.filter(r=>(r.status||'').toLowerCase()==='open').length;
  const completed = rows.filter(r=>{const s=(r.status||'').toLowerCase(); return s==='completed'||s==='closed';}).length;
  const overdue = rows.filter(r=>{
    if((r.status||'').toLowerCase()!=='open') return false;
    const d=ctParseAct(r.due); return d && d<today;
  }).length;
  const people = new Set(rows.map(r=>r.assigned).filter(Boolean)).size;
  if(document.getElementById('ctKpiTotal'))     document.getElementById('ctKpiTotal').textContent     = rows.length;
  if(document.getElementById('ctKpiOpen'))      document.getElementById('ctKpiOpen').textContent      = open;
  if(document.getElementById('ctKpiOverdue'))   document.getElementById('ctKpiOverdue').textContent   = overdue;
  if(document.getElementById('ctKpiCompleted'))document.getElementById('ctKpiCompleted').textContent= completed;
  if(document.getElementById('ctKpiPeople'))   document.getElementById('ctKpiPeople').textContent   = people;

  // By task type
  function mkBreak(keyFn, hdr, top){
    const m={}; rows.forEach(r=>{const k=keyFn(r); if(!k) return; m[k]=(m[k]||0)+1;});
    let entries=Object.entries(m).sort((a,b)=>b[1]-a[1]);
    if(top) entries=entries.slice(0,top);
    let h='<table class="break-table"><thead><tr><th>'+hdr+'</th><th># Tasks</th><th>%</th></tr></thead><tbody>';
    entries.forEach(([k,v])=>h+='<tr><td>'+esc(k)+'</td><td class="num">'+v+'</td><td class="num">'+(rows.length>0?(v/rows.length*100).toFixed(1)+'%':'0%')+'</td></tr>');
    h+='<tr class="total-row"><td>Total</td><td class="num">'+rows.length+'</td><td class="num">100%</td></tr></tbody></table>';
    return h;
  }
  if(document.getElementById('ctTypeTable'))    document.getElementById('ctTypeTable').innerHTML    = mkBreak(r=>r.task_type, 'Task Type');
  if(document.getElementById('ctStatusTable'))  document.getElementById('ctStatusTable').innerHTML  = mkBreak(r=>r.status,    'Status');
  if(document.getElementById('ctAssignedTable'))document.getElementById('ctAssignedTable').innerHTML= mkBreak(r=>r.assigned, 'Assigned To', 12);
  if(document.getElementById('ctAssocTable'))   document.getElementById('ctAssocTable').innerHTML   = mkBreak(r=>r.assoc,    'Entity');

  // Monthly trend (last 6)
  const months=[]; for(let i=5;i>=0;i--){const d=new Date(TODAY.getFullYear(),TODAY.getMonth()-i,1);months.push({label:d.toLocaleString('default',{month:'short',year:'2-digit'}),from:d,to:eom(d)});}
  let h='<table class="trend-table"><thead><tr><th>Metric</th>';
  months.forEach(m=>h+='<th>'+m.label+'</th>'); h+='</tr></thead><tbody>';
  const metrics=[
    {label:'New Tasks',       fn:(rs)=>rs.length},
    {label:'Open',            fn:(rs)=>rs.filter(r=>(r.status||'').toLowerCase()==='open').length},
    {label:'Completed',       fn:(rs)=>rs.filter(r=>{const s=(r.status||'').toLowerCase();return s==='completed'||s==='closed';}).length},
  ];
  metrics.forEach(m=>{
    h+='<tr><td class="metric-name">'+m.label+'</td>';
    months.forEach(mo=>{
      const subset=CTROWS.filter(r=>{const d=ctParseAct(r.activity);return d&&d>=mo.from&&d<=mo.to;});
      h+='<td class="num">'+m.fn(subset)+'</td>';
    });
    h+='</tr>';
  });
  h+='</tbody></table>';
  if(document.getElementById('ctTrendTable')) document.getElementById('ctTrendTable').innerHTML=h;

  // Task list (with expand)
  let ht='<div class="table-wrap"><table><thead><tr><th style="width:36px"></th>'
        +'<th>Activity Date</th><th>Subject</th><th>Type</th><th>Status</th>'
        +'<th>Assoc</th><th>Created By</th><th>Assigned To</th><th>Due</th><th>Reminder</th></tr></thead><tbody>';
  const pg=rows.slice(0,300);
  if(!pg.length) ht+='<tr><td colspan="10" class="no-data">No tasks match the selected filters.</td></tr>';
  pg.forEach(r=>{
    const isOpen=ctExpanded.has(r.id);
    const arrow=isOpen?'&#9660;':'&#9658;';
    const stLow=(r.status||'').toLowerCase();
    const stColor = stLow==='open'?'#f59e0b':(stLow==='completed'||stLow==='closed'?'#10b981':'#6b7280');
    const due=ctParseAct(r.due); const isOver=due&&due<today&&stLow==='open';
    ht+='<tr style="cursor:pointer" onclick="ctToggle(\''+esc(r.id)+'\')">'
      +'<td style="text-align:center;color:#1a6ec0;font-weight:700">'+arrow+'</td>'
      +'<td style="white-space:nowrap;font-size:11px">'+esc(r.activity)+'</td>'
      +'<td>'+esc(r.subject)+'</td>'
      +'<td><span style="display:inline-block;padding:2px 8px;background:#eef3f9;color:#1a3a5c;border-radius:10px;font-size:11px;font-weight:600">'+esc(r.task_type)+'</span></td>'
      +'<td><span style="display:inline-block;padding:2px 8px;background:'+stColor+';color:#fff;border-radius:10px;font-size:11px;font-weight:600">'+esc(r.status)+'</span></td>'
      +'<td>'+esc(r.assoc)+'</td>'
      +'<td>'+esc(r.created_by)+'</td>'
      +'<td>'+esc(r.assigned)+'</td>'
      +'<td style="white-space:nowrap;'+(isOver?'color:#dc2626;font-weight:600':'')+'">'+esc(r.due)+(isOver?' &#9888;':'')+'</td>'
      +'<td style="white-space:nowrap;font-size:11px">'+esc(r.reminder)+'</td></tr>';
    if(isOpen){
      ht+='<tr><td colspan="10" style="padding:10px 14px;background:#f5f8fc;border-left:3px solid #1a6ec0">'
        +'<div style="font-weight:600;color:#1a3a5c;margin-bottom:4px">Note:</div>'
        +'<div style="white-space:pre-wrap;font-size:12.5px">'+esc(r.text)+'</div></td></tr>';
    }
  });
  ht+='</tbody></table></div>';
  if(rows.length>300) ht+='<div class="page-info" style="margin-top:6px">Showing 300 of '+rows.length+' tasks. Use filters to narrow.</div>';
  if(document.getElementById('ctTableWrap')) document.getElementById('ctTableWrap').innerHTML=ht;
}

/* ═══════════════════════════════════════════════════════════════
   UTILIZATION REVIEW LOGIC
═══════════════════════════════════════════════════════════════ */
let AROWS = JSON.parse(document.getElementById('authData').textContent);

function aFilter(rows,from,to){return rows.filter(r=>{const d=pd(r.adm);return d&&d>=from&&d<=to;});}
function aMetrics(rows){
  const auths=new Set(rows.filter(r=>r.code).map(r=>r.code)).size;
  const au=rows.reduce((s,r)=>s+r.au,0);
  const bu=rows.reduce((s,r)=>s+r.bu,0);
  return{auths,au:Math.round(au),bu:Math.round(bu),rem:Math.round(au-bu),util:au>0?bu/au:0,avg:auths>0?au/auths:0};
}
const UR_PERIODS=MKT_PERIODS;
const UR_METRICS=[
  {key:'auths',label:'# Authorizations',fmt:v=>v.toLocaleString()},
  {key:'au',label:'Total Authorized Units',fmt:v=>v.toLocaleString()},
  {key:'bu',label:'Total Billed Units',fmt:v=>v.toLocaleString()},
  {key:'rem',label:'Remaining Units',fmt:v=>v.toLocaleString()},
  {key:'util',label:'Auth Utilization %',fmt:fmtPct},
  {key:'avg',label:'Avg Units per Auth',fmt:v=>v.toFixed(1)},
];

function renderURSpot(){
  let h='<table class="spot-table"><thead><tr><th>Metric</th>';
  UR_PERIODS.forEach(p=>h+='<th>'+p.label+'</th>'); h+='</tr></thead><tbody>';
  UR_METRICS.forEach(m=>{
    h+='<tr><td class="metric-name">'+m.label+'</td>';
    UR_PERIODS.forEach(p=>{const c=aMetrics(aFilter(AROWS,p.from(),p.to()));h+='<td class="num">'+m.fmt(c[m.key])+'</td>';});
    h+='</tr>';
  });
  h+='</tbody></table>';
  document.getElementById('urSpot').innerHTML=h;
  // Upcoming reviews
  const now=new Date(TODAY);
  const thresholds=[{label:'Overdue',days:-1},{label:'Due Today',days:0},{label:'Due in 3 Days',days:3},{label:'Due in 7 Days',days:7},{label:'Due in 14 Days',days:14}];
  let hu='<table class="break-table"><thead><tr><th>Review Status</th><th># Auths</th></tr></thead><tbody>';
  thresholds.forEach(t=>{
    const cnt=AROWS.filter(r=>{
      const d=pd(r.nrd);if(!d)return false;
      const diff=Math.floor((d-now)/86400000);
      if(t.days<0)return diff<0;
      if(t.days===0)return diff===0;
      return diff>0&&diff<=t.days;
    }).length;
    hu+='<tr><td>'+t.label+'</td><td class="num">'+cnt+'</td></tr>';
  });
  hu+='</tbody></table>';
  document.getElementById('urUpcoming').innerHTML=hu;
}

function renderURTrend(){
  const months=[];for(let i=5;i>=0;i--){const d=new Date(TODAY.getFullYear(),TODAY.getMonth()-i,1);months.push({label:d.toLocaleString('default',{month:'short',year:'2-digit'}),from:d,to:eom(d)});}
  let h='<table class="trend-table"><thead><tr><th>Metric</th>';
  months.forEach(m=>h+='<th>'+m.label+'</th>'); h+='</tr></thead><tbody>';
  UR_METRICS.forEach(m=>{
    h+='<tr><td class="metric-name">'+m.label+'</td>';
    months.forEach(mo=>{const c=aMetrics(aFilter(AROWS,mo.from,mo.to));h+='<td class="num">'+m.fmt(c[m.key])+'</td>';});
    h+='</tr>';
  });
  h+='</tbody></table>';
  document.getElementById('urTrend').innerHTML=h;
  // By insurance (YTD)
  const ytd=aFilter(AROWS,new Date(TODAY.getFullYear(),0,1),TODAY);
  const insMap={};ytd.forEach(r=>{if(r.ins){const au=r.au,bu=r.bu;if(!insMap[r.ins])insMap[r.ins]={auths:new Set(),au:0,bu:0};insMap[r.ins].auths.add(r.code);insMap[r.ins].au+=au;insMap[r.ins].bu+=bu;}});
  let hi='<table class="break-table"><thead><tr><th>Insurance (YTD)</th><th>Auths</th><th>Auth Units</th><th>Billed</th><th>Util %</th></tr></thead><tbody>';
  Object.entries(insMap).sort((a,b)=>b[1].au-a[1].au).forEach(([k,v])=>{
    hi+='<tr><td>'+esc(k)+'</td><td class="num">'+v.auths.size+'</td><td class="num">'+Math.round(v.au)+'</td><td class="num">'+Math.round(v.bu)+'</td><td class="num">'+(v.au>0?(v.bu/v.au*100).toFixed(1)+'%':'0%')+'</td></tr>';
  });
  hi+='</tbody></table>';
  document.getElementById('urInsTable').innerHTML=hi;
  // By reviewer
  const revMap={};ytd.forEach(r=>{if(r.reviewer){if(!revMap[r.reviewer])revMap[r.reviewer]={auths:new Set(),au:0,bu:0};revMap[r.reviewer].auths.add(r.code);revMap[r.reviewer].au+=r.au;revMap[r.reviewer].bu+=r.bu;}});
  let hrev='<table class="break-table"><thead><tr><th>UR Reviewer (YTD)</th><th>Auths</th><th>Auth Units</th><th>Billed</th><th>Util %</th></tr></thead><tbody>';
  Object.entries(revMap).sort((a,b)=>b[1].auths.size-a[1].auths.size).forEach(([k,v])=>{
    hrev+='<tr><td>'+esc(k)+'</td><td class="num">'+v.auths.size+'</td><td class="num">'+Math.round(v.au)+'</td><td class="num">'+Math.round(v.bu)+'</td><td class="num">'+(v.au>0?(v.bu/v.au*100).toFixed(1)+'%':'0%')+'</td></tr>';
  });
  hrev+='</tbody></table>';
  document.getElementById('urRevTable').innerHTML=hrev;
}

/* ═══════════════════════════════════════════════════════════════
   CLINICAL LOGIC
═══════════════════════════════════════════════════════════════ */
let GNROWS = JSON.parse(document.getElementById('gnData').textContent);

function gnFilter(rows,from,to){return rows.filter(r=>{const d=pd(r.date);return d&&d>=from&&d<=to;});}

let clinNavView='all',clinNavDate=null;
for(const r of GNROWS){const d=pd(r.date);if(d){clinNavDate=d;break;}}
if(!clinNavDate)clinNavDate=new Date();

function clinNavRange(){
  if(clinNavView==='all')  return{from:new Date(1900,0,1),to:new Date(2100,0,1)};
  if(clinNavView==='year') return{from:new Date(clinNavDate.getFullYear(),0,1),to:new Date(clinNavDate.getFullYear(),11,31)};
  if(clinNavView==='month')return{from:som(clinNavDate),to:eom(clinNavDate)};
  if(clinNavView==='week'){const ws=gwk(clinNavDate),we=new Date(ws);we.setDate(we.getDate()+6);return{from:ws,to:we};}
  return{from:new Date(clinNavDate),to:new Date(clinNavDate)};
}
function clinNavLabel(){
  if(clinNavView==='all')  return 'All Time';
  if(clinNavView==='year') return String(clinNavDate.getFullYear());
  if(clinNavView==='month')return clinNavDate.toLocaleString('default',{month:'long'})+' '+clinNavDate.getFullYear();
  if(clinNavView==='week'){const{from,to}=clinNavRange();return fd(from)+' \u2013 '+fd(to);}
  return fd(clinNavDate);
}
function clinNavigate(dir){
  if(clinNavView==='all') return;
  if(clinNavView==='year') clinNavDate=new Date(clinNavDate.getFullYear()+dir,0,1);
  else if(clinNavView==='month')clinNavDate=new Date(clinNavDate.getFullYear(),clinNavDate.getMonth()+dir,1);
  else if(clinNavView==='week')clinNavDate=new Date(clinNavDate.getTime()+dir*7*86400000);
  else clinNavDate=new Date(clinNavDate.getTime()+dir*86400000);
  renderClinical();
}
function clinSetView(v){clinNavView=v;renderClinical();}
function clinJump(val){if(!val)return;const p=val.split('-');clinNavDate=new Date(+p[0],+p[1]-1,+p[2]);renderClinical();}

function renderClinicalSpot(){
  const months=[];for(let i=5;i>=0;i--){const d=new Date(TODAY.getFullYear(),TODAY.getMonth()-i,1);months.push({label:d.toLocaleString('default',{month:'short',year:'2-digit'}),from:d,to:eom(d)});}
  let h='<table class="trend-table"><thead><tr><th>Metric</th>';
  months.forEach(m=>h+='<th>'+m.label+'</th>'); h+='</tr></thead><tbody>';
  const clinMetrics=[
    {label:'# Sessions',fn:rs=>rs.length},
    {label:'Total Hours',fn:rs=>(rs.reduce((s,r)=>s+r.mins,0)/60).toFixed(1)},
    {label:'Active Sessions',fn:rs=>rs.filter(r=>r.status==='active').length},
  ];
  clinMetrics.forEach(m=>{
    h+='<tr><td class="metric-name">'+m.label+'</td>';
    months.forEach(mo=>{h+='<td class="num">'+m.fn(gnFilter(GNROWS,mo.from,mo.to))+'</td>';});
    h+='</tr>';
  });
  h+='</tbody></table>';
  document.getElementById('clinTrend').innerHTML=h;
}

function renderClinical(){
  document.getElementById('clinPeriodLabel').innerHTML=clinNavLabel();
  document.getElementById('clinViewMonth').className='view-btn'+(clinNavView==='month'?' active':'');
  document.getElementById('clinViewWeek').className='view-btn'+(clinNavView==='week'?' active':'');
  document.getElementById('clinViewDay').className='view-btn'+(clinNavView==='day'?' active':'');
  document.getElementById('clinViewYear').className='view-btn'+(clinNavView==='year'?' active':'');
  document.getElementById('clinViewAll').className='view-btn'+(clinNavView==='all'?' active':'');
  const{from,to}=clinNavRange();
  const rows=gnFilter(GNROWS,from,to);
  const totalMins=rows.reduce((s,r)=>s+r.mins,0);
  document.getElementById('clinKpiSessions').textContent=rows.length;
  document.getElementById('clinKpiHours').textContent=(totalMins/60).toFixed(1);
  document.getElementById('clinKpiActive').textContent=rows.filter(r=>r.status==='active').length;
  // By group title
  const titleMap={};rows.forEach(r=>{if(r.title)titleMap[r.title]=(titleMap[r.title]||0)+1;});
  let ht='<table class="break-table"><thead><tr><th>Group Title</th><th># Sessions</th><th>Total Hrs</th></tr></thead><tbody>';
  Object.entries(titleMap).sort((a,b)=>b[1]-a[1]).forEach(([k,v])=>{
    const hrs=(rows.filter(r=>r.title===k).reduce((s,r)=>s+r.mins,0)/60).toFixed(1);
    ht+='<tr><td>'+esc(k)+'</td><td class="num">'+v+'</td><td class="num">'+hrs+'</td></tr>';
  });
  ht+='<tr class="total-row"><td>Total</td><td class="num">'+rows.length+'</td><td class="num">'+( totalMins/60).toFixed(1)+'</td></tr></tbody></table>';
  document.getElementById('clinGroupTable').innerHTML=ht;
  // Session list
  let hlist='<div class="table-wrap"><table><thead><tr><th>Date</th><th>Group Title</th><th>Status</th><th>Duration (min)</th></tr></thead><tbody>';
  const sorted=rows.slice().sort((a,b)=>{const da=pd(a.date),db=pd(b.date);return db-da;});
  if(!sorted.length)hlist+='<tr><td colspan="4" class="no-data">No sessions.</td></tr>';
  sorted.forEach(r=>hlist+='<tr><td>'+esc(r.date)+'</td><td>'+esc(r.title)+'</td><td>'+esc(r.status)+'</td><td class="num">'+r.mins+'</td></tr>');
  hlist+='</tbody></table></div>';
  document.getElementById('clinSessionList').innerHTML=hlist;
}

/* ═══════════════════════════════════════════════════════════════
   OPERATIONS LOGIC
═══════════════════════════════════════════════════════════════ */
let OPROWS2 = JSON.parse(document.getElementById('opsData').textContent);

function renderOpsHeatmap(){
  const from=daysAgo(89);
  const rows=OPROWS2.filter(r=>{const d=pd(r.date);return d&&d>=from&&d<=TODAY&&r.hour>=0&&r.dow>=0;});
  const grid=Array(24).fill(null).map(()=>Array(7).fill(0));
  rows.forEach(r=>grid[r.hour][r.dow]++);
  const maxV=Math.max(1,...grid.flat());
  const days=['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
  let h='<table class="heatmap-table"><thead><tr><th class="row-hdr">Hour</th>';
  days.forEach(d=>h+='<th>'+d+'</th>'); h+='<th>Total</th></tr></thead><tbody>';
  // Business hours first (6am-9pm), then rest
  const hours=Array.from({length:24},(_,i)=>(i+6)%24);
  hours.forEach(hr=>{
    const rowTot=grid[hr].reduce((s,v)=>s+v,0);
    const label=(hr===0?'12am':hr<12?hr+'am':hr===12?'12pm':(hr-12)+'pm');
    h+='<tr><td class="row-hdr" style="background:#eef3f9;padding:4px 8px;font-weight:600;text-align:right">'+label+'</td>';
    for(let d=0;d<7;d++){
      const v=grid[hr][d];
      const level=v===0?0:Math.min(6,Math.ceil(v/maxV*6));
      h+='<td class="hm-'+level+'" title="'+days[d]+' '+label+': '+v+' admits">'+(v||'')+'</td>';
    }
    h+='<td style="text-align:center;font-weight:700;background:#f5f8fc">'+(rowTot||'')+'</td></tr>';
  });
  // Totals row
  h+='<tr><td class="row-hdr" style="background:#1a3a5c;color:#fff;padding:5px 8px;font-weight:700">Total</td>';
  for(let d=0;d<7;d++){const tot=grid.reduce((s,row)=>s+row[d],0);h+='<td style="text-align:center;font-weight:700;background:#1a3a5c;color:#fff">'+tot+'</td>';}
  h+='<td style="text-align:center;font-weight:700;background:#0d2a44;color:#fff">'+rows.length+'</td></tr>';
  h+='</tbody></table>';
  document.getElementById('opsHeatmap').innerHTML=h;
}

let opsNavView='all',opsNavDate=null;
for(const r of OPROWS2){const d=pd(r.date);if(d){opsNavDate=d;break;}}
if(!opsNavDate)opsNavDate=new Date();

function opsNavRange(){
  if(opsNavView==='all')  return{from:new Date(1900,0,1),to:new Date(2100,0,1)};
  if(opsNavView==='year') return{from:new Date(opsNavDate.getFullYear(),0,1),to:new Date(opsNavDate.getFullYear(),11,31)};
  if(opsNavView==='month')return{from:som(opsNavDate),to:eom(opsNavDate)};
  if(opsNavView==='week'){const ws=gwk(opsNavDate),we=new Date(ws);we.setDate(we.getDate()+6);return{from:ws,to:we};}
  return{from:new Date(opsNavDate),to:new Date(opsNavDate)};
}
function opsNavLabel(){
  if(opsNavView==='all')  return 'All Time';
  if(opsNavView==='year') return String(opsNavDate.getFullYear());
  if(opsNavView==='month')return opsNavDate.toLocaleString('default',{month:'long'})+' '+opsNavDate.getFullYear();
  if(opsNavView==='week'){const{from,to}=opsNavRange();return fd(from)+' \u2013 '+fd(to);}
  return fd(opsNavDate);
}
function opsNavigate(dir){
  if(opsNavView==='all') return;
  if(opsNavView==='year') opsNavDate=new Date(opsNavDate.getFullYear()+dir,0,1);
  else if(opsNavView==='month')opsNavDate=new Date(opsNavDate.getFullYear(),opsNavDate.getMonth()+dir,1);
  else if(opsNavView==='week')opsNavDate=new Date(opsNavDate.getTime()+dir*7*86400000);
  else opsNavDate=new Date(opsNavDate.getTime()+dir*86400000);
  renderOpsDetail();
}
function opsSetView(v){opsNavView=v;renderOpsDetail();}
function opsJump(val){if(!val)return;const p=val.split('-');opsNavDate=new Date(+p[0],+p[1]-1,+p[2]);renderOpsDetail();}

function renderOpsDetail(){
  document.getElementById('opsPeriodLabel').innerHTML=opsNavLabel();
  document.getElementById('opsViewMonth').className='view-btn'+(opsNavView==='month'?' active':'');
  document.getElementById('opsViewWeek').className='view-btn'+(opsNavView==='week'?' active':'');
  document.getElementById('opsViewDay').className='view-btn'+(opsNavView==='day'?' active':'');
  document.getElementById('opsViewYear').className='view-btn'+(opsNavView==='year'?' active':'');
  document.getElementById('opsViewAll').className='view-btn'+(opsNavView==='all'?' active':'');
  const{from,to}=opsNavRange();
  const rows=OPROWS2.filter(r=>{const d=pd(r.date);return d&&d>=from&&d<=to;});
  document.getElementById('opsKpiAdmits').textContent=rows.length;
  const locs={}; rows.forEach(r=>{if(r.loc)locs[r.loc]=(locs[r.loc]||0)+1;});
  document.getElementById('opsKpiLOC').textContent=Object.entries(locs).sort((a,b)=>b[1]-a[1])[0]?.[0]||'-';
  document.getElementById('opsKpiTopRep').textContent=(()=>{const m={};rows.forEach(r=>{if(r.rep)m[r.rep]=(m[r.rep]||0)+1;});return Object.entries(m).sort((a,b)=>b[1]-a[1])[0]?.[0]||'-';})();

  function mkBreakTable(keyFn,hdr){
    const map={};rows.forEach(r=>{const k=keyFn(r);if(k)map[k]=(map[k]||0)+1;});
    let h='<table class="break-table"><thead><tr><th>'+hdr+'</th><th>Admits</th><th>%</th></tr></thead><tbody>';
    Object.entries(map).sort((a,b)=>b[1]-a[1]).forEach(([k,v])=>h+='<tr><td>'+esc(k)+'</td><td class="num">'+v+'</td><td class="num">'+(rows.length>0?(v/rows.length*100).toFixed(1)+'%':'0%')+'</td></tr>');
    h+='<tr class="total-row"><td>Total</td><td class="num">'+rows.length+'</td><td class="num">100%</td></tr></tbody></table>';
    return h;
  }
  document.getElementById('opsRepTable').innerHTML=mkBreakTable(r=>r.rep,'Admissions Rep');
  document.getElementById('opsTherapistTable').innerHTML=mkBreakTable(r=>r.therapist,'Assigned Therapist');
  document.getElementById('opsInsTable').innerHTML=mkBreakTable(r=>r.ins,'Insurance');
  document.getElementById('opsLocTable').innerHTML=mkBreakTable(r=>r.loc,'Level of Care');
}

function renderOpsMonthlyIns(){
  const months=[];for(let i=5;i>=0;i--){const d=new Date(TODAY.getFullYear(),TODAY.getMonth()-i,1);months.push({label:d.toLocaleString('default',{month:'short',year:'2-digit'}),from:d,to:eom(d)});}
  const insSet=new Set(OPROWS2.map(r=>r.ins).filter(Boolean));
  const topIns=Object.entries((() => {const m={};OPROWS2.forEach(r=>{if(r.ins)m[r.ins]=(m[r.ins]||0)+1;});return m;})()).sort((a,b)=>b[1]-a[1]).slice(0,8).map(([k])=>k);
  let h='<table class="trend-table"><thead><tr><th>Insurance</th>';
  months.forEach(m=>h+='<th>'+m.label+'</th>'); h+='<th>Total</th></tr></thead><tbody>';
  topIns.forEach(ins=>{
    h+='<tr><td class="metric-name">'+esc(ins)+'</td>';
    let tot=0;
    months.forEach(mo=>{const rs=OPROWS2.filter(r=>{const d=pd(r.date);return d&&d>=mo.from&&d<=mo.to&&r.ins===ins;});h+='<td class="num">'+rs.length+'</td>';tot+=rs.length;});
    h+='<td class="num" style="font-weight:700">'+tot+'</td></tr>';
  });
  // Others row
  h+='<tr><td class="metric-name"><em>Others</em></td>';
  let tot=0;
  months.forEach(mo=>{const rs=OPROWS2.filter(r=>{const d=pd(r.date);return d&&d>=mo.from&&d<=mo.to&&!topIns.includes(r.ins);});h+='<td class="num">'+rs.length+'</td>';tot+=rs.length;});
  h+='<td class="num" style="font-weight:700">'+tot+'</td></tr>';
  // Total row
  h+='<tr class="total-row"><td>Total</td>';
  let grandTot=0;
  months.forEach(mo=>{const rs=OPROWS2.filter(r=>{const d=pd(r.date);return d&&d>=mo.from&&d<=mo.to;});h+='<td class="num">'+rs.length+'</td>';grandTot+=rs.length;});
  h+='<td class="num">'+grandTot+'</td></tr></tbody></table>';
  document.getElementById('opsMonthlyIns').innerHTML=h;
}

/* ═══════════════════════════════════════════════════════════════
   FIELD EXPLORER LOGIC
═══════════════════════════════════════════════════════════════ */
function renderFieldExplorer(){
  const sorted=CROWS.slice().sort((a,b)=>{const da=pd(a.adm),db=pd(b.adm);return db-da;});
  const admits=sorted.filter(r=>!r.dis).slice(0,5);
  const discharges=sorted.filter(r=>r.dis).slice(0,5);
  const fields=[
    {label:'Patient Name',fn:r=>r.name},
    {label:'Admission Date',fn:r=>r.adm},
    {label:'Discharge Date',fn:r=>r.dis||'\u2014'},
    {label:'Admission LOC',fn:r=>r.loc},
    {label:'Current LOC',fn:r=>r.cloc},
    {label:'Gender',fn:r=>r.gen},
    {label:'Age',fn:r=>r.age!=null?r.age:''},
    {label:'Primary Drug',fn:r=>r.drug},
    {label:'Referral Source',fn:r=>r.ref},
    {label:'Discharge Type',fn:r=>r.dtype||'\u2014'},
    {label:'Length of Stay',fn:r=>r.los!=null?r.los+' days':'\u2014'},
  ];
  const mkHeader=(recs,type)=>{
    let h='<th class="fe-section-hdr">'+type+'</th>';
    recs.forEach((r,i)=>h+='<th>'+esc(type==='Active Admits'?r.adm:r.dis)+' \u2014 '+esc(r.name.split(' ').slice(-1)[0])+'</th>');
    while(recs.length<5)h+='<th style="opacity:.3">(empty)</th>',recs.push(null);
    return h;
  };
  let h='<div style="overflow-x:auto"><table style="border-collapse:collapse;font-size:12px;width:100%"><thead>';
  h+='<tr><th style="background:#eef3f9;color:#1a3a5c;padding:8px 12px;text-align:left;position:sticky;left:0;z-index:3;min-width:160px">Field</th>';
  const a5=admits.slice(),d5=discharges.slice();
  while(a5.length<5)a5.push(null);while(d5.length<5)d5.push(null);
  a5.forEach((r,i)=>h+='<th style="background:#1a6ec0;color:#fff;padding:8px 10px;min-width:130px;text-align:center">'+(r?'Admit '+( i+1)+' \u2014 '+esc(r.adm):'&mdash;')+'</th>');
  d5.forEach((r,i)=>h+='<th style="background:#217346;color:#fff;padding:8px 10px;min-width:130px;text-align:center">'+(r?'Disch '+( i+1)+' \u2014 '+esc(r.dis):'&mdash;')+'</th>');
  h+='</tr></thead><tbody>';
  fields.forEach((f,ri)=>{
    const bg=ri%2===0?'#fafbfd':'#fff';
    h+='<tr><td style="background:#eef3f9;font-weight:700;padding:7px 12px;position:sticky;left:0;z-index:2;white-space:nowrap">'+f.label+'</td>';
    a5.forEach(r=>h+='<td style="background:'+bg+';padding:6px 10px;text-align:center;border-bottom:1px solid #eee">'+(r?esc(String(f.fn(r))):'')+'</td>');
    d5.forEach(r=>h+='<td style="background:'+bg+';padding:6px 10px;text-align:center;border-bottom:1px solid #eee">'+(r?esc(String(f.fn(r))):'')+'</td>');
    h+='</tr>';
  });
  h+='</tbody></table></div>';
  document.getElementById('feTable').innerHTML=h;
}

// ── Initial renders ────────────────────────────────────────────────────────
function runDashboard(){
  renderBillingSpot();
  renderBillingBreakdowns();
  renderBillingTrend();
  renderBillingDetail();
  renderCensusSpot();
  renderCensusTrend();
  renderCensusBreakdowns();
  renderMarketingSpot();
  renderMarketingTrend();
  renderMarketingDetail();
  renderOpportunities();
  renderReferrals();
  renderCRMTask();
  renderURSpot();
  renderURTrend();
  renderClinicalSpot();
  renderClinical();
  renderOpsHeatmap();
  renderOpsDetail();
  renderOpsMonthlyIns();
  renderFieldExplorer();
  showPage('billing');
}
// Static mode: auto-run. Live mode: build_live.py removes this line.
runDashboard();
"""

# ── HTML ─────────────────────────────────────────────────────────────────────
CENSUS_SECTION = """
<div class="page-section" id="sec-census" style="display:none">
  <div class="main">

    <h2 class="section-title">SPOT / MOST RECENT &mdash; Active Census, Admits &amp; Discharges by Period</h2>
    <div class="spot-wrap" id="cSpotTable"></div>

    <h2 class="section-title" style="margin-top:18px">DISCHARGE TYPE BREAKDOWN (% of in-period discharges)</h2>
    <div class="spot-wrap" id="cDischargeBreakdown"></div>

    <h2 class="section-title" style="margin-top:18px">MONTHLY TREND &mdash; Last 6 Months</h2>
    <div class="trend-wrap"><div id="cTrendTable"></div></div>

    <h2 class="section-title">PERIOD DETAIL &mdash; Breakdowns by Selected Period</h2>
    <div class="controls">
      <div class="view-btns">
        <button id="cViewMonth" class="view-btn"        onclick="cSetView('month')">Month</button>
        <button id="cViewWeek"  class="view-btn"        onclick="cSetView('week')">Week</button>
        <button id="cViewDay"   class="view-btn"        onclick="cSetView('day')">Day</button>
        <button id="cViewYear"  class="view-btn"        onclick="cSetView('year')">Year</button>
        <button id="cViewAll"   class="view-btn active" onclick="cSetView('all')">Show All</button>
      </div>
      <div class="nav-btns">
        <button class="period-nav-btn" onclick="cNavigate(-1)">&#8249;</button>
        <span class="period-label" id="cPeriodLabel"></span>
        <button class="period-nav-btn" onclick="cNavigate(1)">&#8250;</button>
      </div>
      <input type="date" class="date-input" title="Jump to date" onchange="cJump(this.value)">
    </div>

    <div class="stats-bar">
      <div class="stat-card"><div class="val" id="cKpiActive">-</div><div class="lbl">Active Census</div></div>
      <div class="stat-card green"><div class="val" id="cKpiAdmits">-</div><div class="lbl">Admits</div></div>
      <div class="stat-card orange"><div class="val" id="cKpiDischarges">-</div><div class="lbl">Discharges</div></div>
      <div class="stat-card purple"><div class="val" id="cKpiNet">-</div><div class="lbl">Net Growth</div></div>
      <div class="stat-card"><div class="val" id="cKpiLOS">-</div><div class="lbl">Avg LOS</div></div>
    </div>

    <div class="break-grid">
      <div class="break-card"><h3>ADMITS BY GENDER</h3><div id="cGenderTable"></div></div>
      <div class="break-card"><h3>ADMITS BY AGE BUCKET</h3><div id="cAgeTable"></div></div>
    </div>
    <div class="break-grid">
      <div class="break-card"><h3>PRIMARY DRUG OF CHOICE &mdash; % of Admits</h3><div id="cDrugTable"></div></div>
      <div class="break-card"><h3>DISCHARGE TYPE BREAKDOWN</h3><div id="cDtypeTable"></div></div>
    </div>
    <div class="break-grid">
      <div class="break-card"><h3>REFERRAL SOURCES &mdash; Top 10 + Others</h3><div id="cReferralTable"></div></div>
      <div class="break-card"><h3>AVG LENGTH OF STAY (all-time cohort)</h3><div id="cLOSTable"></div></div>
    </div>

  </div>
</div>
"""

BILLING_SECTION = """
<div class="page-section" id="sec-billing" style="display:none">
  <div class="main">

    <h2 class="section-title">SPOT / MOST RECENT &mdash; Revenue &amp; Collections by Deposit Date</h2>
    <div class="spot-wrap" id="bSpotTable"></div>

    <h2 class="section-title" style="margin-top:18px">MONTHLY TREND &mdash; Last 6 Months</h2>
    <div class="trend-wrap"><div id="bTrendTable"></div></div>

    <h2 class="section-title">DETAIL VIEW &mdash; Selected Period</h2>
    <div class="controls">
      <div class="view-btns">
        <button id="bViewMonth" class="view-btn"        onclick="bSetView('month')">Month</button>
        <button id="bViewWeek"  class="view-btn"        onclick="bSetView('week')">Week</button>
        <button id="bViewDay"   class="view-btn"        onclick="bSetView('day')">Day</button>
        <button id="bViewYear"  class="view-btn"        onclick="bSetView('year')">Year</button>
        <button id="bViewAll"   class="view-btn active" onclick="bSetView('all')">Show All</button>
      </div>
      <div class="nav-btns">
        <button class="period-nav-btn" onclick="bNavigate(-1)">&#8249;</button>
        <span class="period-label" id="bPeriodLabel"></span>
        <button class="period-nav-btn" onclick="bNavigate(1)">&#8250;</button>
      </div>
      <input type="date" class="date-input" title="Jump to date" onchange="bJump(this.value)">
      <input type="text" class="search-box" placeholder="Search records..." oninput="bNavSearch=this.value;renderBillingDetail()">
      <button class="export-btn" onclick="bExport()">&#8595; Export CSV</button>
    </div>

    <div class="stats-bar">
      <div class="stat-card"><div class="val" id="bKpiLines">-</div><div class="lbl"># Payment Lines</div></div>
      <div class="stat-card"><div class="val" id="bKpiCharged">-</div><div class="lbl">Charged $</div></div>
      <div class="stat-card green"><div class="val" id="bKpiPaid">-</div><div class="lbl">Paid $</div></div>
      <div class="stat-card orange"><div class="val" id="bKpiCR">-</div><div class="lbl">Collection Rate</div></div>
      <div class="stat-card orange"><div class="val" id="bKpiNR">-</div><div class="lbl">Net Realization</div></div>
      <div class="stat-card"><div class="val" id="bKpiAvg">-</div><div class="lbl">Avg $ / Line</div></div>
    </div>

    <div class="break-grid">
      <div class="break-card"><h3>PAID $ BY PAYER</h3><div id="bPayerTable"></div></div>
      <div class="break-card"><h3>PAID $ BY LEVEL OF CARE</h3><div id="bLocTable"></div></div>
    </div>
    <div class="break-grid" style="grid-template-columns:1fr">
      <div class="break-card"><h3>ADJUSTMENTS &amp; DENIALS $</h3><div id="bAdjTable"></div></div>
    </div>

    <h2 class="section-title">TRANSACTION DETAIL</h2>
    <div id="bDetailTable"></div>

  </div>
</div>
"""

MARKETING_SECTION = """
<div class="page-section" id="sec-marketing" style="display:none">
  <div class="main">
    <h2 class="section-title">SPOT / MOST RECENT &mdash; Opportunity Funnel by Period</h2>
    <div class="spot-wrap" id="mktSpot"></div>
    <h2 class="section-title" style="margin-top:18px">MONTHLY TREND &mdash; Last 6 Months</h2>
    <div class="trend-wrap"><div id="mktTrend"></div></div>
    <h2 class="section-title">PERIOD DETAIL &mdash; Funnel &amp; Breakdowns</h2>
    <div class="controls">
      <div class="view-btns">
        <button id="mktViewMonth" class="view-btn"        onclick="mktSetView('month')">Month</button>
        <button id="mktViewWeek"  class="view-btn"        onclick="mktSetView('week')">Week</button>
        <button id="mktViewDay"   class="view-btn"        onclick="mktSetView('day')">Day</button>
        <button id="mktViewYear"  class="view-btn"        onclick="mktSetView('year')">Year</button>
        <button id="mktViewAll"   class="view-btn active" onclick="mktSetView('all')">Show All</button>
      </div>
      <div class="nav-btns">
        <button class="period-nav-btn" onclick="mktNavigate(-1)">&#8249;</button>
        <span class="period-label" id="mktPeriodLabel"></span>
        <button class="period-nav-btn" onclick="mktNavigate(1)">&#8250;</button>
      </div>
      <input type="date" class="date-input" title="Jump to date" onchange="mktJump(this.value)">
    </div>
    <div class="stats-bar">
      <div class="stat-card"><div class="val" id="mktKpiTotal">-</div><div class="lbl">Total Created</div></div>
      <div class="stat-card green"><div class="val" id="mktKpiAdmitted">-</div><div class="lbl">Admitted</div></div>
      <div class="stat-card orange"><div class="val" id="mktKpiRate">-</div><div class="lbl">Admit Rate</div></div>
      <div class="stat-card"><div class="val" id="mktKpiActive">-</div><div class="lbl">Active</div></div>
      <div class="stat-card purple"><div class="val" id="mktKpiLost">-</div><div class="lbl">Lost</div></div>
      <div class="stat-card purple"><div class="val" id="mktKpiAbandoned">-</div><div class="lbl">Abandoned</div></div>
    </div>
    <div class="break-grid" style="grid-template-columns:1fr 1fr">
      <div class="break-card"><h3>CONVERSION FUNNEL</h3><div id="mktFunnel"></div></div>
      <div class="break-card"><h3>TOP REFERRAL SOURCES (Admitted)</h3><div id="mktRefTable"></div></div>
    </div>
    <div class="break-grid">
      <div class="break-card"><h3>LOST REASONS</h3><div id="mktLostTable"></div></div>
      <div class="break-card"><h3>ABANDONED REASONS</h3><div id="mktAbandTable"></div></div>
    </div>
  </div>
</div>
"""

OPPORTUNITIES_SECTION = """
<div class="page-section" id="sec-opportunities" style="display:none">
  <div class="main">
    <h2 class="section-title">OPPORTUNITIES DETAIL &mdash; Period View</h2>
    <div class="controls">
      <div class="view-btns">
        <button id="oppViewMonth" class="view-btn"        onclick="oppSetView('month')">Month</button>
        <button id="oppViewWeek"  class="view-btn"        onclick="oppSetView('week')">Week</button>
        <button id="oppViewDay"   class="view-btn"        onclick="oppSetView('day')">Day</button>
        <button id="oppViewYear"  class="view-btn"        onclick="oppSetView('year')">Year</button>
        <button id="oppViewAll"   class="view-btn active" onclick="oppSetView('all')">Show All</button>
      </div>
      <div class="nav-btns">
        <button class="period-nav-btn" onclick="oppNavigate(-1)">&#8249;</button>
        <span class="period-label" id="oppPeriodLabel"></span>
        <button class="period-nav-btn" onclick="oppNavigate(1)">&#8250;</button>
      </div>
      <input type="date" class="date-input" title="Jump to date" onchange="oppJump(this.value)">
      <input type="text" class="search-box" placeholder="Search opportunities..." oninput="oppSearch=this.value;renderOpportunities()">
    </div>
    <div class="stats-bar">
      <div class="stat-card"><div class="val" id="oppKpiTotal">-</div><div class="lbl">Total</div></div>
      <div class="stat-card green"><div class="val" id="oppKpiAdmitted">-</div><div class="lbl">Admitted</div></div>
      <div class="stat-card orange"><div class="val" id="oppKpiRate">-</div><div class="lbl">Admit Rate</div></div>
      <div class="stat-card"><div class="val" id="oppKpiActive">-</div><div class="lbl">Active</div></div>
    </div>
    <div class="break-grid">
      <div class="break-card"><h3>BY OUTCOME</h3><div id="oppOutcomeTable"></div></div>
      <div class="break-card"><h3>BY INSURANCE (Top 10)</h3><div id="oppInsTable"></div></div>
    </div>
    <h2 class="section-title">OPPORTUNITY LIST</h2>
    <div id="oppTableWrap"></div>
  </div>
</div>
"""

UR_SECTION = """
<div class="page-section" id="sec-ur" style="display:none">
  <div class="main">
    <h2 class="section-title">SPOT / MOST RECENT &mdash; Auth Metrics by Period</h2>
    <div class="spot-wrap" id="urSpot"></div>
    <div class="break-grid" style="margin-top:14px">
      <div class="break-card"><h3>UPCOMING REVIEW DATES</h3><div id="urUpcoming"></div></div>
      <div class="break-card"><h3>BY INSURANCE (YTD)</h3><div id="urInsTable"></div></div>
    </div>
    <h2 class="section-title" style="margin-top:18px">MONTHLY TREND &mdash; Last 6 Months</h2>
    <div class="trend-wrap"><div id="urTrend"></div></div>
    <div class="break-grid" style="grid-template-columns:1fr">
      <div class="break-card"><h3>BY UR REVIEWER (YTD)</h3><div id="urRevTable"></div></div>
    </div>
  </div>
</div>
"""

CLINICAL_SECTION = """
<div class="page-section" id="sec-clinical" style="display:none">
  <div class="main">
    <h2 class="section-title">GROUP NOTES TREND &mdash; Last 6 Months</h2>
    <div class="trend-wrap"><div id="clinTrend"></div></div>
    <h2 class="section-title">PERIOD DETAIL</h2>
    <div class="controls">
      <div class="view-btns">
        <button id="clinViewMonth" class="view-btn"        onclick="clinSetView('month')">Month</button>
        <button id="clinViewWeek"  class="view-btn"        onclick="clinSetView('week')">Week</button>
        <button id="clinViewDay"   class="view-btn"        onclick="clinSetView('day')">Day</button>
        <button id="clinViewYear"  class="view-btn"        onclick="clinSetView('year')">Year</button>
        <button id="clinViewAll"   class="view-btn active" onclick="clinSetView('all')">Show All</button>
      </div>
      <div class="nav-btns">
        <button class="period-nav-btn" onclick="clinNavigate(-1)">&#8249;</button>
        <span class="period-label" id="clinPeriodLabel"></span>
        <button class="period-nav-btn" onclick="clinNavigate(1)">&#8250;</button>
      </div>
      <input type="date" class="date-input" title="Jump to date" onchange="clinJump(this.value)">
    </div>
    <div class="stats-bar">
      <div class="stat-card"><div class="val" id="clinKpiSessions">-</div><div class="lbl"># Sessions</div></div>
      <div class="stat-card green"><div class="val" id="clinKpiHours">-</div><div class="lbl">Total Hours</div></div>
      <div class="stat-card orange"><div class="val" id="clinKpiActive">-</div><div class="lbl">Active Sessions</div></div>
    </div>
    <div class="break-grid" style="grid-template-columns:1fr">
      <div class="break-card"><h3>BY GROUP TITLE</h3><div id="clinGroupTable"></div></div>
    </div>
    <h2 class="section-title">SESSION LIST</h2>
    <div id="clinSessionList"></div>
  </div>
</div>
"""

OPERATIONS_SECTION = """
<div class="page-section" id="sec-operations" style="display:none">
  <div class="main">
    <h2 class="section-title">ADMISSION HEATMAP &mdash; Hour &times; Day of Week (Last 90 Days)</h2>
    <div class="heatmap-wrap"><div id="opsHeatmap"></div></div>
    <h2 class="section-title">MONTHLY INSURANCE MIX &mdash; Top 8 Insurers</h2>
    <div class="trend-wrap"><div id="opsMonthlyIns"></div></div>
    <h2 class="section-title">PERIOD DETAIL</h2>
    <div class="controls">
      <div class="view-btns">
        <button id="opsViewMonth" class="view-btn"        onclick="opsSetView('month')">Month</button>
        <button id="opsViewWeek"  class="view-btn"        onclick="opsSetView('week')">Week</button>
        <button id="opsViewDay"   class="view-btn"        onclick="opsSetView('day')">Day</button>
        <button id="opsViewYear"  class="view-btn"        onclick="opsSetView('year')">Year</button>
        <button id="opsViewAll"   class="view-btn active" onclick="opsSetView('all')">Show All</button>
      </div>
      <div class="nav-btns">
        <button class="period-nav-btn" onclick="opsNavigate(-1)">&#8249;</button>
        <span class="period-label" id="opsPeriodLabel"></span>
        <button class="period-nav-btn" onclick="opsNavigate(1)">&#8250;</button>
      </div>
      <input type="date" class="date-input" title="Jump to date" onchange="opsJump(this.value)">
    </div>
    <div class="stats-bar">
      <div class="stat-card"><div class="val" id="opsKpiAdmits">-</div><div class="lbl">Admits</div></div>
      <div class="stat-card green"><div class="val" id="opsKpiLOC">-</div><div class="lbl">Top LOC</div></div>
      <div class="stat-card orange"><div class="val" id="opsKpiTopRep">-</div><div class="lbl">Top Admissions Rep</div></div>
    </div>
    <div class="break-grid">
      <div class="break-card"><h3>BY ADMISSIONS REP</h3><div id="opsRepTable"></div></div>
      <div class="break-card"><h3>BY ASSIGNED THERAPIST</h3><div id="opsTherapistTable"></div></div>
    </div>
    <div class="break-grid">
      <div class="break-card"><h3>BY INSURANCE</h3><div id="opsInsTable"></div></div>
      <div class="break-card"><h3>BY LEVEL OF CARE</h3><div id="opsLocTable"></div></div>
    </div>
  </div>
</div>
"""

FIELD_EXPLORER_SECTION = """
<div class="page-section" id="sec-fieldexplorer" style="display:none">
  <div class="main">
    <h2 class="section-title">FIELD EXPLORER &mdash; 5 Most Recent Admits &amp; Discharges</h2>
    <div class="trend-wrap"><div id="feTable"></div></div>
  </div>
</div>
"""

CRM_TASK_SECTION = """
<div class="page-section" id="sec-crmtask" style="display:none">
  <div class="main">
    <h2 class="section-title">CRM TASKS &mdash; Sunwave Timeline</h2>
    <div class="controls">
      <div class="view-btns">
        <button id="ctViewMonth" class="view-btn"        onclick="ctSetView('month')">Month</button>
        <button id="ctViewWeek"  class="view-btn"        onclick="ctSetView('week')">Week</button>
        <button id="ctViewDay"   class="view-btn"        onclick="ctSetView('day')">Day</button>
        <button id="ctViewYear"  class="view-btn"        onclick="ctSetView('year')">Year</button>
        <button id="ctViewAll"   class="view-btn active" onclick="ctSetView('all')">Show All</button>
      </div>
      <div class="nav-btns">
        <button class="period-nav-btn" onclick="ctNavigate(-1)">&#8249;</button>
        <span class="period-label" id="ctPeriodLabel"></span>
        <button class="period-nav-btn" onclick="ctNavigate(1)">&#8250;</button>
      </div>
      <input type="date" class="date-input" title="Jump to date" onchange="ctJump(this.value)">
      <select class="date-input" id="ctStatusSel" onchange="ctStatus=this.value;renderCRMTask()">
        <option value="">All Statuses</option>
        <option>Open</option><option>Completed</option><option>In Progress</option><option>Closed</option>
      </select>
      <select class="date-input" id="ctTypeSel" onchange="ctType=this.value;renderCRMTask()">
        <option value="">All Task Types</option>
        <option>Call</option><option>Email</option><option>Text</option><option>Online</option><option>In Person</option>
      </select>
      <select class="date-input" id="ctAssocSel" onchange="ctAssoc=this.value;renderCRMTask()">
        <option value="">All Entities</option>
        <option>Referral</option><option>Opportunity</option><option>Patient</option>
      </select>
      <input type="text" class="search-box" placeholder="Search subject, text, names..." oninput="ctSearch=this.value;renderCRMTask()">
      <button class="export-btn" onclick="ctExport()">&#8595; Export CSV</button>
    </div>
    <div class="stats-bar">
      <div class="stat-card"><div class="val" id="ctKpiTotal">-</div><div class="lbl">Total Tasks</div></div>
      <div class="stat-card green"><div class="val" id="ctKpiOpen">-</div><div class="lbl">Open</div></div>
      <div class="stat-card orange"><div class="val" id="ctKpiOverdue">-</div><div class="lbl">Overdue</div></div>
      <div class="stat-card"><div class="val" id="ctKpiCompleted">-</div><div class="lbl">Completed</div></div>
      <div class="stat-card purple"><div class="val" id="ctKpiPeople">-</div><div class="lbl">People Assigned</div></div>
    </div>
    <div class="break-grid">
      <div class="break-card"><h3>BY TASK TYPE</h3><div id="ctTypeTable"></div></div>
      <div class="break-card"><h3>BY STATUS</h3><div id="ctStatusTable"></div></div>
    </div>
    <div class="break-grid">
      <div class="break-card"><h3>BY ASSIGNED TO (TOP 12)</h3><div id="ctAssignedTable"></div></div>
      <div class="break-card"><h3>BY ASSOCIATED ENTITY</h3><div id="ctAssocTable"></div></div>
    </div>
    <h2 class="section-title" style="margin-top:18px">MONTHLY TREND &mdash; Last 6 Months</h2>
    <div class="trend-wrap"><div id="ctTrendTable"></div></div>
    <h2 class="section-title">TASK LIST &mdash; click row to expand full note</h2>
    <div id="ctTableWrap"></div>
  </div>
</div>
"""

REFERRAL_SECTION = """
<div class="page-section" id="sec-referral" style="display:none">
  <div class="main">
    <h2 class="section-title">REFERRAL ACTIVE &mdash; Period View</h2>
    <div class="controls">
      <div class="view-btns">
        <button id="refViewMonth" class="view-btn"        onclick="refSetView('month')">Month</button>
        <button id="refViewWeek"  class="view-btn"        onclick="refSetView('week')">Week</button>
        <button id="refViewDay"   class="view-btn"        onclick="refSetView('day')">Day</button>
        <button id="refViewYear"  class="view-btn"        onclick="refSetView('year')">Year</button>
        <button id="refViewAll"   class="view-btn active" onclick="refSetView('all')">Show All</button>
      </div>
      <div class="nav-btns">
        <button class="period-nav-btn" onclick="refNavigate(-1)">&#8249;</button>
        <span class="period-label" id="refPeriodLabel"></span>
        <button class="period-nav-btn" onclick="refNavigate(1)">&#8250;</button>
      </div>
      <input type="date" class="date-input" title="Jump to date" onchange="refJump(this.value)">
      <input type="text" class="search-box" placeholder="Search referrals..." oninput="refSearch=this.value;renderReferrals()">
    </div>
    <div class="stats-bar">
      <div class="stat-card"><div class="val" id="refKpiTotal">-</div><div class="lbl">Active Referrals</div></div>
      <div class="stat-card green"><div class="val" id="refKpiTimeline">-</div><div class="lbl">Timeline Entries</div></div>
      <div class="stat-card orange"><div class="val" id="refKpiTypes">-</div><div class="lbl">Distinct Types</div></div>
    </div>
    <div class="break-grid">
      <div class="break-card"><h3>BY REFERRAL TYPE</h3><div id="refTypeTable"></div></div>
      <div class="break-card"><h3>BY OWNER</h3><div id="refOwnerTable"></div></div>
    </div>
    <h2 class="section-title">REFERRAL LIST &mdash; click row to expand timeline</h2>
    <div id="refTableWrap"></div>
  </div>
</div>
"""

html = (
    '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
    '<meta charset="UTF-8">\n'
    '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
    '<title>Sunwave Dashboard</title>\n'
    '<style>' + CSS + '</style>\n'
    '</head>\n<body>\n'
    '<div id="app">\n'

    # Topbar (navy) — brand + actions only
    '  <div id="topbar">\n'
    '    <div class="brand">\n'
    '      <span class="brand-pill">SUNWAVE</span>\n'
    '      <div class="brand-text"><span class="name">Sunwave Dashboard</span><span class="sub">Provident Healthcare Management</span></div>\n'
    '    </div>\n'
    '    <div style="flex:1"></div>\n'
    '    <button class="topbar-action" onclick="toggleTabsMenu(event)" title="Show / hide tabs">&#9881;&nbsp; Tabs</button>\n'
    '    <button class="topbar-action" onclick="doRefresh()" title="Refresh data">&#8635;&nbsp; Refresh</button>\n'
    '  </div>\n'
    # Tab bar (white) — sticky below topbar
    '  <nav id="tabBar"></nav>\n'
    '  <div id="tabsMenu" class="tabs-menu"></div>\n'

    # Main: filter rail + content
    '  <div id="main">\n'
    '    <aside id="filterRail">\n'
    '      <h3>Filters</h3>\n'
    '      <div id="filterContent"></div>\n'
    '    </aside>\n'
    '    <div id="content">\n'
    '      <div class="page-header">\n'
    '        <div><h2 id="pageTitle">AR / Billing Dashboard</h2>\n'
    '             <small id="pageSub">Payment Report Deposit Date</small></div>\n'
    '        <div class="page-actions">\n'
    '          <button class="page-action-btn green" onclick="exportPageToExcel()" title="Export current page tables to Excel">&#8595;&nbsp; Excel</button>\n'
    '          <button class="page-action-btn blue"  onclick="exportPageToPNG()"  title="Download current page as PNG image">&#8595;&nbsp; PNG</button>\n'
    '        </div>\n'
    '      </div>\n'
    '      <div id="sectionsWrap">\n'
    + BILLING_SECTION
    + CENSUS_SECTION
    + MARKETING_SECTION
    + OPPORTUNITIES_SECTION
    + REFERRAL_SECTION
    + CRM_TASK_SECTION
    + UR_SECTION
    + CLINICAL_SECTION
    + OPERATIONS_SECTION
    + FIELD_EXPLORER_SECTION +
    '      </div>\n'
    '    </div>\n'
    '  </div>\n'
    '</div>\n'

    # External libs
    '<script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"></script>\n'
    '<script src="https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js"></script>\n'
    '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>\n'

    # Data
    '<script type="application/json" id="buildInfo">' + build_info_js + '</script>\n'
    '<script type="application/json" id="generalData">' + general_js + '</script>\n'
    '<script type="application/json" id="dateIdx">'     + config_js  + '</script>\n'
    '<script type="application/json" id="billingData">' + billing_js + '</script>\n'
    '<script type="application/json" id="censusData">'  + census_js  + '</script>\n'
    '<script type="application/json" id="oppData">'     + opp_js     + '</script>\n'
    '<script type="application/json" id="authData">'    + auth_js    + '</script>\n'
    '<script type="application/json" id="opsData">'     + ops_js     + '</script>\n'
    '<script type="application/json" id="gnData">'      + gnotes_js  + '</script>\n'
    '<script type="application/json" id="tlData">'       + timeline_js+ '</script>\n'
    '<script type="application/json" id="refData">'      + referral_js+ '</script>\n'
    '<script type="application/json" id="crmTaskData">'  + crm_task_js+ '</script>\n'
    '<script>' + JS + '</script>\n'
    '</body>\n</html>'
)

# ── Inject silent background-refresh script + cache-override pre-processor ──
# Goal: page loads instantly with embedded data (no loader). On every load,
# in the background, try a silent SSO via MSAL — if user is already signed in
# to M365 in this browser, fetch fresh data from Graph API and store it in
# localStorage. Subsequent loads use the cached newer data automatically.
CLIENT_ID       = 'debd63be-2397-4d6e-adb1-381574e7352b'
TENANT_ID       = '063ab74f-56d1-429a-b96d-a24a572025de'
SHAREPOINT_HOST = 'gshealthcarellc.sharepoint.com'
SITE_PATH       = 'sites/Provident'
FILE_NAME       = 'MASTER_Sunwave_New_PowerQuerry.xlsx'

PRE_PROCESSOR = """
(function(){
  // If localStorage holds newer/cached data from a prior background refresh,
  // overwrite the embedded placeholders BEFORE the dashboard JS parses them.
  try {
    const c = JSON.parse(localStorage.getItem('sunwave_data_v3') || 'null');
    if (!c || !c.data) return;
    const map = {
      generalData: 'raw_data', dateIdx: 'tab_config', billingData: 'billing_rows',
      censusData:  'census_rows', oppData: 'opp_rows', authData: 'auth_rows',
      opsData:     'ops_rows', gnData: 'gn_rows', tlData: 'timeline_rows',
    };
    Object.entries(map).forEach(([id, key]) => {
      if (c.data[key] !== undefined) {
        const el = document.getElementById(id);
        if (el) el.textContent = JSON.stringify(c.data[key]);
      }
    });
  } catch(e) { console.warn('Cache pre-load skipped:', e); }
})();
"""

BG_REFRESH = ("""
(function(){
  const SCOPES = ['Files.Read', 'Sites.Read.All'];
  const HOST = '__HOST__', SITE = '__SITE__', FILE = '__FILE__';
  const cfg = { auth: {
    clientId: '__CID__',
    authority: 'https://login.microsoftonline.com/__TID__',
    redirectUri: window.location.origin + window.location.pathname,
  }, cache: { cacheLocation: 'localStorage' } };

  function xDate(v){
    if (v===null||v===undefined||v==='') return '';
    if (typeof v==='number'){ const d=new Date(Math.round((v-25569)*86400000));
      return String(d.getUTCMonth()+1).padStart(2,'0')+'/'+String(d.getUTCDate()).padStart(2,'0')+'/'+d.getUTCFullYear(); }
    return String(v).trim();
  }
  function xDT(v){
    if (typeof v==='number'){ const d=new Date(Math.round((v-25569)*86400000));
      const hr=d.getUTCHours(),mn=d.getUTCMinutes(),ap=hr>=12?'PM':'AM',h12=hr%12===0?12:hr%12;
      return String(d.getUTCMonth()+1).padStart(2,'0')+'/'+String(d.getUTCDate()).padStart(2,'0')+'/'+d.getUTCFullYear()
        +' '+String(h12).padStart(2,'0')+':'+String(mn).padStart(2,'0')+' '+ap; }
    return v?String(v).trim():'';
  }
  const xN=v=>{if(v===null||v===undefined||v==='')return 0;const n=parseFloat(v);return isNaN(n)?0:Math.round(n*100)/100;};
  const xI=v=>{if(v===null||v===undefined||v==='')return null;const n=parseFloat(v);return isNaN(n)?null:Math.round(n);};
  const xS=v=>v==null?'':String(v).trim();
  function dow(v){if(typeof v!=='number')return -1;const d=new Date(Math.round((v-25569)*86400000));return d.getUTCDay();}
  function hr(v){if(typeof v==='number')return Math.floor(v*24)%24;const m=String(v||'').match(/(\\d{1,2}):/);return m?+m[1]:-1;}

  async function gget(p,t){
    const r=await fetch('https://graph.microsoft.com/v1.0'+p,{headers:{Authorization:'Bearer '+t}});
    if(!r.ok) throw new Error('Graph '+r.status);
    return r.json();
  }

  function map(sheets, name, fn){
    const v=sheets[name]; if(!v||v.length<2) return [];
    const cols=v[0].map(c=>xS(c));
    const i=c=>cols.indexOf(c);
    const out=[]; for(let k=1;k<v.length;k++) out.push(fn(v[k], i));
    return out;
  }
  function transform(sheets){
    const DF={'Census':'Admission Date','Census Active':'Admission Date','Census_Admitted':'Admission Date','Census_Discharge':'Discharge Date','GroupNotes':'session_date','Incident Report':'incident_reports.date_of_incident','Opportunities Active':'created_on','Opportunities by Created Date':'created_on','Opportunities':'created_on','Patients':'created_on','Payment Report Payment Date':'payment_date','Payment Report Deposit Date':'deposit_date','Referral Active':'created_on','Report Auth':'admission_date','Report Deleted Form':'deleted_on','Report Diagnois Changes':'date_from','Report Form Modified':'modified_on','Report Program Change':'start_on','Report UR Changes':'admission_date','Users':'created_on'};
    const SK=['Table of Contents','Realms','Bedboard','Payment Summary'];
    const HINT=['date','_on','admission','discharge','deposit','review','modified','deleted'];
    const raw_data={}, tab_config={};
    for(const [n,v] of Object.entries(sheets)){
      if(SK.includes(n)||!v||!v.length) continue;
      const cols=v[0].map(c=>xS(c));
      const dIdxs=cols.map((c,i)=>HINT.some(h=>c.toLowerCase().includes(h))?i:-1).filter(i=>i>=0);
      const rows=v.slice(1).map(r=>r.map((c,i)=>{
        if(c==null) return '';
        if(typeof c==='number'&&dIdxs.includes(i)&&c>25000&&c<80000) return xDate(c);
        return String(c);
      }));
      raw_data[n]={columns:cols,rows};
      const dc=DF[n];
      tab_config[n]=(dc&&cols.indexOf(dc)>=0)?cols.indexOf(dc):-1;
    }
    return {
      raw_data, tab_config,
      billing_rows: map(sheets,'Payment Report Deposit Date',(r,i)=>({deposit_date:xDate(r[i('deposit_date')]),payer_name:xS(r[i('payer_name')]),level_of_care:xS(r[i('level_of_care')]),adjustment_type:xS(r[i('adjustment_type')]),service_facility:xS(r[i('service_facility')]),service_name:xS(r[i('service_name')]),payment_type:xS(r[i('payment_type')]),line_charge_amount:xN(r[i('line_charge_amount')]),line_paid_amount:xN(r[i('line_paid_amount')]),line_adjusted:xN(r[i('line_adjusted')]),line_allocated_amount:xN(r[i('line_allocated_amount')]),line_patient_name:xS(r[i('line_patient_name')]),procedure_code:xS(r[i('procedure_code')])})),
      census_rows: map(sheets,'Census',(r,i)=>({adm:xDate(r[i('Admission Date')]),dis:xDate(r[i('Discharge Date')]),loc:xS(r[i('Admission Level Of Care')]),cloc:xS(r[i('Current Level Of Care')]),gen:xS(r[i('Patient Gender Code')]),age:xI(r[i('Age')]),drug:xS(r[i('Primary Drug Of Choice ')]),ref:xS(r[i('Referral Source')]),dtype:xS(r[i('Discharge Type')]),los:xI(r[i('Length Of Stay')]),name:xS(r[i('Patient Name')])})),
      opp_rows: map(sheets,'Opportunities by Created Date',(r,i)=>{const a=r[i('admission_date')];const ok=typeof a==='number'?a>36500:true;return {id:xS(r[i('opportunity_id')]),co:xDate(r[i('created_on')]),adm:ok?xDate(a):'',outcome:xS(r[i('outcome')]),stage:xS(r[i('stage')]),loc:xS(r[i('level_of_care')]),ins:xS(r[i('insurance provider')]),ref:xS(r[i('referral name')]),lost_r:xS(r[i('lost reason')]),aband_r:xS(r[i('abandoned reason')]),name:xS(r[i('patient name')])};}),
      auth_rows: map(sheets,'Report Auth',(r,i)=>({adm:xDate(r[i('admission_date')]),nrd:xDate(r[i('next_review_date')]),code:xS(r[i('authorization_code')]),au:xN(r[i('authorized_units')]),bu:xN(r[i('billed_units_total')]),ins:xS(r[i('insurance_provider')]),reviewer:xS(r[i('ur_reviewer')]),patient:xS(r[i('patient_name')]),facility:xS(r[i('service_facility')])})),
      ops_rows: map(sheets,'Census_Admitted',(r,i)=>({date:xDate(r[i('Admission Date')]),hour:hr(r[i('Admission Time')]),dow:dow(r[i('Admission Date')]),rep:xS(r[i('Admissions Rep')]),therapist:xS(r[i('Assigned Therapist')]),ins:xS(r[i('Insurance Name')]),loc:xS(r[i('Admission Level Of Care')]),name:xS(r[i('Patient Name')])})),
      gn_rows: map(sheets,'GroupNotes',(r,i)=>({date:xDate(r[i('session_date')]),title:xS(r[i('group_title')]),status:xS(r[i('status')]),mins:Math.round(parseFloat(r[i('length_time')])||0)})),
      timeline_rows: map(sheets,'Timeline',(r,i)=>({oid:xS(r[i('opportunity_id')]),date:xDT(r[i('activity_date')]),subject:xS(r[i('task_subject')]),type:xS(r[i('type')]),by:xS(r[i('created_by_name')]),wf:xS(r[i('workflow_status')]),text:xS(r[i('text')]),sortKey:typeof r[i('activity_date')]==='number'?r[i('activity_date')]:0})),
      crm_rows: map(sheets,'CRM Task',(r,i)=>({id:xS(r[i('id')]),aid:xS(r[i('Associated_id')]),assoc:xS(r[i('associated_with')]),subject:xS(r[i('task_subject')]),type:xS(r[i('type')]),task_type:xS(r[i('task_type')]),status:xS(r[i('task_status')]),created_by:xS(r[i('created_by_name')]),assigned:xS(r[i('assigned_to_name')]),text:xS(r[i('text')]),activity:typeof r[i('activity_date')]==='number'?xDT(r[i('activity_date')]):xS(r[i('activity_date')]),due:typeof r[i('task_due_date')]==='number'?xDT(r[i('task_due_date')]):xS(r[i('task_due_date')]),reminder:typeof r[i('reminder_date_time')]==='number'?xDT(r[i('reminder_date_time')]):xS(r[i('reminder_date_time')]),sortKey:typeof r[i('activity_date')]==='number'?r[i('activity_date')]:0})),
    };
  }

  function applyLiveData(data){
    // Update module-level data variables so all render functions use fresh data
    if(data.raw_data)     RAW      = data.raw_data;
    if(data.tab_config)   DATE_IDX = data.tab_config;
    if(data.billing_rows) BROWS    = data.billing_rows;
    if(data.census_rows)  CROWS    = data.census_rows;
    if(data.opp_rows)     { OROWS = data.opp_rows; TLROWS = data.timeline_rows||TLROWS; }
    if(data.auth_rows)    AROWS    = data.auth_rows;
    if(data.gn_rows)      GNROWS   = data.gn_rows;
    if(data.ops_rows)     OPROWS2  = data.ops_rows;
    if(data.crm_rows)     CTROWS   = data.crm_rows;
    SHEETS = Object.keys(RAW);
    // Re-initialize bNavDate from fresh billing data
    if(data.billing_rows && data.billing_rows.length){
      for(const r of BROWS){ const d=pd(r.deposit_date); if(d){if(!bNavDate||d>bNavDate)bNavDate=d;break;} }
    }
    // Re-render the currently visible tab
    doRefresh();
  }

  async function bgRefresh(){
    if(!window.msal){ setTimeout(bgRefresh, 300); return; }
    try{
      const inst = new msal.PublicClientApplication(cfg);
      if(typeof inst.initialize==='function') await inst.initialize();
      let account = inst.getAllAccounts()[0];
      let token;
      if(account){
        const r = await inst.acquireTokenSilent({scopes:SCOPES, account});
        token = r.accessToken;
      } else {
        try {
          const r = await inst.ssoSilent({scopes:SCOPES});
          token = r.accessToken;
        } catch(e){
          // No silent SSO available — user not signed in. Skip refresh.
          console.log('[bg refresh] silent SSO unavailable, skipping');
          return;
        }
      }
      // Fetch and transform
      const site = await gget('/sites/'+HOST+':/'+SITE, token);
      const search = await gget('/sites/'+site.id+"/drive/root/search(q='"+encodeURIComponent(FILE)+"')", token);
      const file = (search.value||[]).find(f=>f.name===FILE) || (search.value||[])[0];
      if(!file) return;
      const ws = await gget('/sites/'+site.id+'/drive/items/'+file.id+'/workbook/worksheets', token);
      const names = ws.value.map(w=>w.name);
      const sheets = {};
      await Promise.all(names.map(async n => {
        try { const r = await gget('/sites/'+site.id+'/drive/items/'+file.id+'/workbook/worksheets/'+encodeURIComponent(n)+'/usedRange?$select=values', token);
          sheets[n] = r.values || []; } catch(e){ sheets[n] = []; }
      }));
      const data = transform(sheets);
      const _ts = Date.now();
      localStorage.setItem('sunwave_data_v3', JSON.stringify({v:3, ts: _ts, data}));
      console.log('[bg refresh] cache updated — applying live data');
      // Apply fresh data immediately (no reload needed)
      applyLiveData(data);
      // Update the displayed sync timestamp on all tabs
      const _sub = document.getElementById('pageSub');
      if(_sub && typeof fmtSyncedAt === 'function') _sub.textContent = fmtSyncedAt(_ts);
    } catch(e){
      console.warn('[bg refresh] failed silently:', e);
    }
  }

  // Kick off after page paints, never blocking UI
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded', ()=>setTimeout(bgRefresh,500));
  else setTimeout(bgRefresh,500);
})();
"""
.replace('__CID__',  CLIENT_ID)
.replace('__TID__',  TENANT_ID)
.replace('__HOST__', SHAREPOINT_HOST)
.replace('__SITE__', SITE_PATH)
.replace('__FILE__', FILE_NAME))

# Insert pre-processor BEFORE the dashboard JS so cached data overrides
# placeholders before parsing. Insert bg refresh AFTER dashboard JS + MSAL CDN.
INJECT = (
    '<script>' + PRE_PROCESSOR + '</script>\n'
    '<script src="https://cdn.jsdelivr.net/npm/@azure/msal-browser@3.10.0/lib/msal-browser.min.js"></script>\n'
    '<script>if(!window.msal){document.write(\'<script src="https://unpkg.com/@azure/msal-browser@3.10.0/lib/msal-browser.min.js"><\\/script>\');}</script>\n'
    '<script>' + BG_REFRESH + '</script>\n'
)
html = html.replace('<script>' + JS + '</script>\n',
                    '<script>' + PRE_PROCESSOR + '</script>\n<script>' + JS + '</script>\n'
                    '<script src="https://cdn.jsdelivr.net/npm/@azure/msal-browser@3.10.0/lib/msal-browser.min.js"></script>\n'
                    '<script>if(!window.msal){document.write(\'<script src="https://unpkg.com/@azure/msal-browser@3.10.0/lib/msal-browser.min.js"><\\/script>\');}</script>\n'
                    '<script>' + BG_REFRESH + '</script>\n')

# Write both the labelled file and index.html for GitHub Pages
for out in ('Sunwave_Dashboard.html', 'index.html'):
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
print(f"Done: {os.path.getsize('index.html')/1024/1024:.1f} MB (also wrote Sunwave_Dashboard.html)")

# ── Sub-pages ──────────────────────────────────────────────────────────────────
_SUB_NAV = [
    ('billing',       'Billing',        'billing'),
    ('census',        'Census',         'census'),
    ('marketing',     'Marketing',      'marketing'),
    ('opportunities', 'Opportunities',  'opportunities'),
    ('referral',      'Referrals',      'referral'),
    ('crmtask',       'CRM Tasks',      'crmtask'),
    ('ur',            'UR',             'ur'),
    ('clinical',      'Clinical',       'clinical'),
    ('operations',    'Operations',     'operations'),
    ('fieldexplorer', 'Field Explorer', 'fieldexplorer'),
]

def _make_subnav(active_id):
    parts = []
    for sid, lbl, folder in _SUB_NAV:
        cls = 'tab-btn active' if sid == active_id else 'tab-btn'
        parts.append(f'<a href="../{folder}/" class="{cls}">{lbl}</a>')
    parts.append('<a href="../crm/" class="tab-btn">CRM</a>')
    return ''.join(parts)

print('Generating sub-pages...')
for _sid, _lbl, _folder in _SUB_NAV:
    _nav    = _make_subnav(_sid)
    _home = 'https://providentanalytics.github.io/Sunwave/'
    _inject = (
        f'<script>(function(){{'
        f'var bar=document.getElementById("tabBar");'
        f'if(bar)bar.innerHTML={json.dumps(_nav)};'
        f'var brand=document.querySelector(".brand");'
        f'if(brand){{brand.style.cursor="pointer";brand.title="Go to home";'
        f'brand.addEventListener("click",function(){{window.location.href={json.dumps(_home)};}});}}'
        f'if(typeof showPage==="function")showPage("{_sid}");'
        f'}})();</script>\n'
        f'</body>\n</html>'
    )
    _content = html.replace('</body>\n</html>', _inject, 1)
    os.makedirs(_folder, exist_ok=True)
    with open(f'{_folder}/index.html', 'w', encoding='utf-8') as _f:
        _f.write(_content)
    print(f'  {_folder}/index.html  ({os.path.getsize(f"{_folder}/index.html")/1024:.0f} KB)')

# Overwrite root index.html with a lightweight redirect to billing/
_redirect = (
    '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
    '<meta charset="UTF-8">\n'
    '<meta http-equiv="refresh" content="0;url=billing/">\n'
    '<title>Sunwave Dashboard</title>\n'
    '</head>\n<body>\n'
    '<p>Redirecting to <a href="billing/">Sunwave Dashboard</a>…</p>\n'
    '</body>\n</html>\n'
)
with open('index.html', 'w', encoding='utf-8') as _f:
    _f.write(_redirect)
print('  index.html  (redirect -> billing/)')
print('Sub-pages done.')
