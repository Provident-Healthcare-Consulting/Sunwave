"""build_crm.py — generate Sunwave CRM Dashboard at crm/index.html.

Reads data from SQL views (vw_excel_*) via pyodbc.

Inputs:
  - SQL views: vw_excel_opportunities_by_created_date, vw_excel_timeline
  - dashboard_template_crm.html

Output:
  - crm/index.html
"""
import json
import os
import re
import math
import pandas as pd
from datetime import datetime, timezone
from db import get_connection

conn = get_connection()
print('[CRM] Connected to SQL database')


def safe_str(v):
    if v is None:
        return ''
    if isinstance(v, float) and math.isnan(v):
        return ''
    s = str(v).strip()
    return '' if s.lower() in ('nan', 'nat', 'none') else s


def fmt_dt(v):
    if v is None or pd.isna(v):
        return ''
    if hasattr(v, 'isoformat'):
        try:
            return v.isoformat()
        except Exception:
            pass
    return safe_str(v)


# ── Process Opportunities ───────────────────────────────────────────────────
print('[CRM] Loading Opportunities from SQL...')
odf = pd.read_sql('SELECT * FROM dbo.vw_excel_opportunities_by_created_date', conn)
print(f'  {len(odf)} rows from vw_excel_opportunities_by_created_date')
for c in ('created_on', 'admission_date'):
    if c in odf.columns:
        odf[c] = pd.to_datetime(odf[c], errors='coerce')
opps = []
for _, r in odf.iterrows():
    oid = safe_str(r.get('opportunity_id') or r.get('opportunity_legacy_id') or r.get('id'))
    if not oid:
        continue
    co = r.get('created_on'); ad = r.get('admission_date')
    opps.append({
        'id':      oid,
        'name':    safe_str(r.get('patient name') or r.get('Patient Name') or ''),
        'co':      fmt_dt(co),
        'admit':   fmt_dt(ad),
        'outcome': safe_str(r.get('outcome')),
        'stage':   safe_str(r.get('stage')),
        'loc':     safe_str(r.get('level_of_care')),
        'ins':     safe_str(r.get('insurance provider')),
        'ref':     safe_str(r.get('referral name')),
        'lost_r':  safe_str(r.get('lost reason')),
        'aband_r': safe_str(r.get('abandoned reason')),
        'rep':     safe_str(r.get('adm. representative')),
    })
print(f'  Opps: {len(opps)} rows')


# ── Process Timeline (activities) ──────────────────────────────────────────
print('[CRM] Loading Timeline from SQL...')
tdf = pd.read_sql('SELECT * FROM dbo.vw_excel_timeline', conn)
print(f'  {len(tdf)} rows from vw_excel_timeline')
for c in ('activity_date', 'task_due_date', 'reminder_date_time', 'created_on', 'orig_activity_date'):
    if c in tdf.columns:
        tdf[c] = pd.to_datetime(tdf[c], errors='coerce')

acts = []
for _, r in tdf.iterrows():
    oid = safe_str(r.get('opportunity_id')) or safe_str(r.get('associated_with_id'))
    typ = safe_str(r.get('type'))
    if not (oid or typ):
        continue
    acts.append({
        'oid':   oid,
        'aid':   safe_str(r.get('id')),
        'type':  typ,
        'subj':  safe_str(r.get('task_subject'))[:140],
        'text':  safe_str(r.get('text'))[:400],
        'by':    safe_str(r.get('created_by_name')),
        'wf':    safe_str(r.get('workflow_status')),
        'date':  fmt_dt(r.get('activity_date')),
        'assoc': safe_str(r.get('associated_with')),
        'task_type':         safe_str(r.get('task_type')),
        'task_status':       safe_str(r.get('task_status')),
        'task_due_date':     fmt_dt(r.get('task_due_date')),
        'reminder_date_time':fmt_dt(r.get('reminder_date_time')),
        'assigned_to_name':  safe_str(r.get('assigned_to_name')),
    })
print(f'  Acts: {len(acts)} rows')


# ── Derive Users from Timeline (created_by_name + assigned_to_name) ────────
print('[CRM] Deriving Users from Timeline...')
user_set = {}
for a in acts:
    for nm in (a.get('by'), a.get('assigned_to_name')):
        nm = safe_str(nm)
        if not nm:
            continue
        key = nm.lower()
        if key not in user_set:
            user_set[key] = {'id': '', 'name': nm, 'email': '', 'role': '', 'count': 0}
        user_set[key]['count'] += 1
users = sorted(user_set.values(), key=lambda u: -u['count'])
print(f'  Users: {len(users)}')


# ── Derive open CRM Tasks from Timeline (type='Task') ──────────────────────
print('[CRM] Deriving Tasks from Timeline rows where type=Task...')
tasks = []
for _, r in tdf.iterrows():
    if safe_str(r.get('type')) != 'Task':
        continue
    status = safe_str(r.get('task_status')).lower()
    is_open = status in ('open', 'pending', '') and status not in ('completed', 'closed', 'cancelled')
    tasks.append({
        'id':         safe_str(r.get('id')),
        'aid':        safe_str(r.get('associated_with_id') or r.get('opportunity_id')),
        'assoc':      safe_str(r.get('associated_with')),
        'subject':    safe_str(r.get('task_subject')),
        'task_type':  safe_str(r.get('task_type')),
        'status':     safe_str(r.get('task_status')),
        'created_by': safe_str(r.get('created_by_name')),
        'assigned':   safe_str(r.get('assigned_to_name')),
        'text':       safe_str(r.get('text'))[:400],
        'due':        fmt_dt(r.get('task_due_date')),
        'created':    fmt_dt(r.get('created_on')),
        'reminder':   fmt_dt(r.get('reminder_date_time')),
        'is_open':    is_open,
    })
print(f'  Tasks: {len(tasks)} (open={sum(1 for t in tasks if t["is_open"])})')


# ── Meta ────────────────────────────────────────────────────────────────────
meta = {
    'refreshed_at': datetime.now(timezone.utc).isoformat(),
    'opps_count':   len(opps),
    'acts_count':   len(acts),
    'users_count':  len(users),
    'tasks_count':  len(tasks),
    'open_tasks':   sum(1 for t in tasks if t['is_open']),
}

conn.close()

# ── Build HTML ──────────────────────────────────────────────────────────────
template_path = 'dashboard_template_crm.html'
if not os.path.exists(template_path):
    raise SystemExit(f'Template not found: {template_path}')

with open(template_path, 'r', encoding='utf-8') as f:
    html = f.read()

sep = (',', ':')
replacements = {
    '/*INJECT_OPPS*/null':  json.dumps(opps,  separators=sep, ensure_ascii=True),
    '/*INJECT_ACTS*/null':  json.dumps(acts,  separators=sep, ensure_ascii=True),
    '/*INJECT_USERS*/null': json.dumps(users, separators=sep, ensure_ascii=True),
    '/*INJECT_TASKS*/null': json.dumps(tasks, separators=sep, ensure_ascii=True),
    '/*INJECT_META*/null':  json.dumps(meta,  separators=sep, ensure_ascii=True),
}
for placeholder, value in replacements.items():
    if placeholder not in html:
        print(f'Warning: placeholder {placeholder} not found in template')
    html = html.replace(placeholder, value)

errors = []
if '/*INJECT_' in html:
    errors.append('Some /*INJECT_*/ placeholders remained unfilled')

os.makedirs('crm', exist_ok=True)
out_path = os.path.join('crm', 'index.html')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'\nWrote {out_path}: {os.path.getsize(out_path)//1024} KB')
print(f'  opps={len(opps)} acts={len(acts)} users={len(users)} '
      f'tasks={len(tasks)} (open={meta["open_tasks"]})')
if errors:
    print('Pre-push checks FAILED:')
    for e in errors:
        print('  -', e)
    raise SystemExit(1)
print('Pre-push checks: OK')
