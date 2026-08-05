"""fetch_sql.py — query SQL views and generate report_data.json.

Replaces fetch_excel.py: instead of downloading an Excel workbook from
SharePoint, queries the vw_excel_* views in Azure SQL and produces the
same report_data.json shape that build_combined.py expects.

Env vars required (see db.py):
  SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASSWORD
"""
import json, os
import pandas as pd
from db import get_connection

VIEW_MAP = {
    'Census':                         'dbo.vw_excel_census',
    'Census Active':                  'dbo.vw_excel_census_active',
    'Census_Admitted':                'dbo.vw_excel_census_admitted',
    'Census_Discharge':               'dbo.vw_excel_census_discharge',
    'GroupNotes':                      'dbo.vw_excel_group_notes',
    'Incident Report':                 'dbo.vw_excel_incident_report',
    'Opportunities':                   'dbo.vw_excel_opportunities',
    'Opportunities Active':            'dbo.vw_excel_opportunities_active',
    'Opportunities by Created Date':   'dbo.vw_excel_opportunities_by_created_date',
    'Patients':                        'dbo.vw_excel_patients',
    'Payment Report Deposit Date':     'dbo.vw_excel_payment_report_deposit_date',
    'Payment Report Payment Date':     'dbo.vw_excel_payment_report_payment_date',
    'Referral Active':                 'dbo.vw_excel_referral_active',
    'Report Auth':                     'dbo.vw_excel_report_auth',
    'Report Deleted Form':             'dbo.vw_excel_report_deleted_form',
    'Report Diagnois Changes':         'dbo.vw_excel_report_diagnosis_changes',
    'Report Form Modified':            'dbo.vw_excel_report_form_modified',
    'Report Program Change':           'dbo.vw_excel_report_program_change',
    'Report UR Changes':               'dbo.vw_excel_report_ur_changes',
    'Users':                           'dbo.vw_excel_users',
    'CRM Task':                        'dbo.vw_excel_crm_task',
    'Timeline':                        'dbo.vw_excel_timeline',
}

def build_report_data():
    conn = get_connection()
    out = {}
    for sheet_name, view_name in VIEW_MAP.items():
        print(f'[SQL] Querying {view_name} for "{sheet_name}"...')
        try:
            df = pd.read_sql(f'SELECT * FROM {view_name}', conn)
        except Exception as e:
            print(f'  Warning: {view_name} failed: {e}')
            continue
        for c in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[c]):
                df[c] = df[c].dt.strftime('%m/%d/%Y').fillna('')
        df = df.where(pd.notna(df), '')
        out[sheet_name] = {
            'columns': [str(c) for c in df.columns],
            'rows': df.astype(str).values.tolist(),
        }
        print(f'  {sheet_name}: {len(df)} rows')
    conn.close()

    with open('report_data.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, default=str)
    size_mb = os.path.getsize('report_data.json') / 1024 / 1024
    print(f'Wrote report_data.json: {size_mb:.1f} MB')


if __name__ == '__main__':
    build_report_data()
    print('Done.')
