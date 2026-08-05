const { app } = require('@azure/functions');
const { query } = require('../db');

function safe(v) {
  if (v === null || v === undefined) return '';
  if (typeof v === 'number' && isNaN(v)) return '';
  const s = String(v).trim();
  return s === 'null' || s === 'NaN' || s === 'None' ? '' : s;
}

function fmtDate(v) {
  if (!v) return '';
  if (v instanceof Date) {
    if (isNaN(v.getTime())) return '';
    const m = String(v.getMonth() + 1).padStart(2, '0');
    const d = String(v.getDate()).padStart(2, '0');
    return `${v.getFullYear()}-${m}-${d}`;
  }
  return safe(v);
}

function fmtDateTime(v) {
  if (!v) return '';
  if (v instanceof Date) {
    if (isNaN(v.getTime())) return '';
    return v.toISOString();
  }
  return safe(v);
}

function num(v) {
  if (v === null || v === undefined) return 0;
  const n = Number(v);
  return isNaN(n) ? 0 : n;
}

// ── Generic view endpoint ──────────────────────────────────────────────────

const VIEW_MAP = {
  'billing': 'vw_excel_payment_report_deposit_date',
  'census': 'vw_excel_census',
  'census-active': 'vw_excel_census_active',
  'census-admitted': 'vw_excel_census_admitted',
  'census-discharge': 'vw_excel_census_discharge',
  'group-notes': 'vw_excel_group_notes',
  'incident-report': 'vw_excel_incident_report',
  'opportunities': 'vw_excel_opportunities',
  'opportunities-active': 'vw_excel_opportunities_active',
  'opportunities-created': 'vw_excel_opportunities_by_created_date',
  'patients': 'vw_excel_patients',
  'payment-deposit': 'vw_excel_payment_report_deposit_date',
  'payment-date': 'vw_excel_payment_report_payment_date',
  'referrals': 'vw_excel_referral_active',
  'auth': 'vw_excel_report_auth',
  'deleted-forms': 'vw_excel_report_deleted_form',
  'diagnosis-changes': 'vw_excel_report_diagnosis_changes',
  'form-modified': 'vw_excel_report_form_modified',
  'program-change': 'vw_excel_report_program_change',
  'ur-changes': 'vw_excel_report_ur_changes',
  'users': 'vw_excel_users',
  'crm-tasks': 'vw_excel_crm_task',
  'timeline': 'vw_excel_timeline',
};

app.http('dashboard-view', {
  methods: ['GET'],
  authLevel: 'anonymous',
  route: 'dashboard/view/{name}',
  handler: async (request, context) => {
    const name = request.params.name;
    const viewName = VIEW_MAP[name];
    if (!viewName) {
      return { status: 404, jsonBody: { error: `Unknown view: ${name}`, available: Object.keys(VIEW_MAP) } };
    }
    try {
      const result = await query(`SELECT * FROM dbo.${viewName}`);
      return { jsonBody: result.recordset };
    } catch (err) {
      context.error(`dashboard-view [${name}]:`, err.message);
      return { status: 500, jsonBody: { error: err.message } };
    }
  },
});

// ── CRM dashboard endpoint ─────────────────────────────────────────────────

app.http('dashboard-crm', {
  methods: ['GET'],
  authLevel: 'anonymous',
  route: 'dashboard/crm',
  handler: async (request, context) => {
    try {
      const [oppsResult, tlResult] = await Promise.all([
        query('SELECT * FROM dbo.vw_excel_opportunities_by_created_date'),
        query('SELECT * FROM dbo.vw_excel_timeline'),
      ]);

      const opps = oppsResult.recordset.map(r => {
        const oid = safe(r.opportunity_id || r.opportunity_legacy_id || r.id);
        if (!oid) return null;
        return {
          id: oid,
          name: safe(r['patient name'] || r['Patient Name']),
          co: fmtDateTime(r.created_on),
          admit: fmtDateTime(r.admission_date),
          outcome: safe(r.outcome),
          stage: safe(r.stage),
          loc: safe(r.level_of_care),
          ins: safe(r['insurance provider']),
          ref: safe(r['referral name']),
          lost_r: safe(r['lost reason']),
          aband_r: safe(r['abandoned reason']),
          rep: safe(r['adm. representative']),
        };
      }).filter(Boolean);

      const acts = [];
      const userSet = {};
      const tasks = [];

      for (const r of tlResult.recordset) {
        const oid = safe(r.opportunity_id) || safe(r.associated_with_id);
        const typ = safe(r.type);
        if (!oid && !typ) continue;

        const by = safe(r.created_by_name);
        const assigned = safe(r.assigned_to_name);

        acts.push({
          oid,
          aid: safe(r.id),
          type: typ,
          subj: safe(r.task_subject).slice(0, 140),
          text: safe(r.text).slice(0, 400),
          by,
          wf: safe(r.workflow_status),
          date: fmtDateTime(r.activity_date),
          assoc: safe(r.associated_with),
          task_type: safe(r.task_type),
          task_status: safe(r.task_status),
          task_due_date: fmtDateTime(r.task_due_date),
          reminder_date_time: fmtDateTime(r.reminder_date_time),
          assigned_to_name: assigned,
        });

        for (const nm of [by, assigned]) {
          if (!nm) continue;
          const key = nm.toLowerCase();
          if (!userSet[key]) userSet[key] = { id: '', name: nm, email: '', role: '', count: 0 };
          userSet[key].count++;
        }

        if (typ === 'Task') {
          const status = safe(r.task_status).toLowerCase();
          const isOpen = ['open', 'pending', ''].includes(status) && !['completed', 'closed', 'cancelled'].includes(status);
          tasks.push({
            id: safe(r.id),
            aid: safe(r.associated_with_id || r.opportunity_id),
            assoc: safe(r.associated_with),
            subject: safe(r.task_subject),
            task_type: safe(r.task_type),
            status: safe(r.task_status),
            created_by: by,
            assigned,
            text: safe(r.text).slice(0, 400),
            due: fmtDateTime(r.task_due_date),
            created: fmtDateTime(r.created_on),
            reminder: fmtDateTime(r.reminder_date_time),
            is_open: isOpen,
          });
        }
      }

      const users = Object.values(userSet).sort((a, b) => b.count - a.count);

      return {
        jsonBody: {
          opps,
          acts,
          users,
          tasks,
          meta: {
            refreshed_at: new Date().toISOString(),
            opps_count: opps.length,
            acts_count: acts.length,
            users_count: users.length,
            tasks_count: tasks.length,
            open_tasks: tasks.filter(t => t.is_open).length,
          },
        },
      };
    } catch (err) {
      context.error('dashboard-crm:', err.message);
      return { status: 500, jsonBody: { error: err.message } };
    }
  },
});

// ── UR dashboard endpoint ──────────────────────────────────────────────────

app.http('dashboard-ur', {
  methods: ['GET'],
  authLevel: 'anonymous',
  route: 'dashboard/ur',
  handler: async (request, context) => {
    try {
      const [authResult, censusResult, gnotesResult] = await Promise.all([
        query('SELECT * FROM dbo.vw_excel_report_auth'),
        query('SELECT * FROM dbo.vw_excel_census_admitted'),
        query('SELECT * FROM dbo.vw_excel_group_notes'),
      ]);

      const auths = authResult.recordset.map(r => {
        const au = num(r.authorized_units);
        const bu = num(r.billed_units_total);
        return {
          patient: safe(r.patient_name),
          facility: safe(r.service_facility),
          adm: fmtDate(r.admission_date),
          nrd: fmtDate(r.next_review_date),
          code: safe(r.authorization_code),
          au: Math.round(au * 10) / 10,
          bu: Math.round(bu * 10) / 10,
          util: au > 0 ? Math.round(bu / au * 1000) / 10 : null,
          ins: safe(r.insurance_provider),
          reviewer: safe(r.ur_reviewer),
        };
      });

      const census = censusResult.recordset.map(r => ({
        patient: safe(r['Patient Name']),
        adm: fmtDate(r['Admission Date']),
        loc: safe(r['Admission Level Of Care']),
        ins: safe(r['Insurance Name']),
        rep: safe(r['Admissions Rep']),
        therapist: safe(r['Assigned Therapist']),
      }));

      const gnotes = gnotesResult.recordset.map(r => ({
        patient: safe(r.patient_name),
        date: fmtDate(r.session_date),
        title: safe(r.group_title),
        status: safe(r.status),
        mins: Math.round(num(r.length_time)),
      }));

      return {
        jsonBody: {
          auths,
          census,
          gnotes,
          meta: {
            refreshed_at: new Date().toISOString(),
            total_auths: auths.length,
            total_census: census.length,
            total_groupnotes: gnotes.length,
          },
        },
      };
    } catch (err) {
      context.error('dashboard-ur:', err.message);
      return { status: 500, jsonBody: { error: err.message } };
    }
  },
});

// ── Billing dashboard endpoint ─────────────────────────────────────────────

app.http('dashboard-billing', {
  methods: ['GET'],
  authLevel: 'anonymous',
  route: 'dashboard/billing',
  handler: async (request, context) => {
    try {
      const result = await query('SELECT * FROM dbo.vw_excel_payment_report_deposit_date');
      const rows = result.recordset.map(r => {
        const dep = r.deposit_date;
        let depStr = '';
        if (dep instanceof Date && !isNaN(dep.getTime())) {
          depStr = `${String(dep.getMonth() + 1).padStart(2, '0')}/${String(dep.getDate()).padStart(2, '0')}/${dep.getFullYear()}`;
        }
        return {
          deposit_date: depStr,
          payer_name: safe(r.payer_name),
          level_of_care: safe(r.level_of_care),
          adjustment_type: safe(r.adjustment_type),
          service_facility: safe(r.service_facility),
          service_name: safe(r.service_name),
          payment_type: safe(r.payment_type),
          line_charge_amount: Math.round(num(r.line_charge_amount) * 100) / 100,
          line_paid_amount: Math.round(num(r.line_paid_amount) * 100) / 100,
          line_adjusted: Math.round(num(r.line_adjusted) * 100) / 100,
          line_allocated_amount: Math.round(num(r.line_allocated_amount) * 100) / 100,
          line_patient_name: safe(r.line_patient_name),
          procedure_code: safe(r.procedure_code),
        };
      });
      return { jsonBody: rows };
    } catch (err) {
      context.error('dashboard-billing:', err.message);
      return { status: 500, jsonBody: { error: err.message } };
    }
  },
});

// ── Combined dashboard endpoint ────────────────────────────────────────────

app.http('dashboard-combined', {
  methods: ['GET'],
  authLevel: 'anonymous',
  route: 'dashboard/combined',
  handler: async (request, context) => {
    try {
      const [billing, census, opps, timeline, auth, admitted, gnotes, crmTask, referrals] = await Promise.all([
        query('SELECT * FROM dbo.vw_excel_payment_report_deposit_date'),
        query('SELECT * FROM dbo.vw_excel_census'),
        query('SELECT * FROM dbo.vw_excel_opportunities_by_created_date'),
        query('SELECT * FROM dbo.vw_excel_timeline'),
        query('SELECT * FROM dbo.vw_excel_report_auth'),
        query('SELECT * FROM dbo.vw_excel_census_admitted'),
        query('SELECT * FROM dbo.vw_excel_group_notes'),
        query('SELECT * FROM dbo.vw_excel_crm_task'),
        query('SELECT * FROM dbo.vw_excel_referral_active'),
      ]);

      function fmtMmDd(v) {
        if (!v || !(v instanceof Date) || isNaN(v.getTime())) return '';
        return `${String(v.getMonth() + 1).padStart(2, '0')}/${String(v.getDate()).padStart(2, '0')}/${v.getFullYear()}`;
      }
      function fmtMmDdTime(v) {
        if (!v || !(v instanceof Date) || isNaN(v.getTime())) return '';
        let h = v.getHours(), ampm = h >= 12 ? 'PM' : 'AM';
        h = h % 12 || 12;
        return `${fmtMmDd(v)} ${h}:${String(v.getMinutes()).padStart(2, '0')} ${ampm}`;
      }

      const billingRows = billing.recordset.map(r => ({
        deposit_date: fmtMmDd(r.deposit_date),
        payer_name: safe(r.payer_name),
        level_of_care: safe(r.level_of_care),
        adjustment_type: safe(r.adjustment_type),
        service_facility: safe(r.service_facility),
        service_name: safe(r.service_name),
        payment_type: safe(r.payment_type),
        line_charge_amount: Math.round(num(r.line_charge_amount) * 100) / 100,
        line_paid_amount: Math.round(num(r.line_paid_amount) * 100) / 100,
        line_adjusted: Math.round(num(r.line_adjusted) * 100) / 100,
        line_allocated_amount: Math.round(num(r.line_allocated_amount) * 100) / 100,
        line_patient_name: safe(r.line_patient_name),
        procedure_code: safe(r.procedure_code),
      }));

      const censusRows = census.recordset.map(r => ({
        adm: fmtMmDd(r['Admission Date']),
        dis: fmtMmDd(r['Discharge Date']),
        loc: safe(r['Admission Level Of Care']),
        cloc: safe(r['Current Level Of Care']),
        gen: safe(r['Patient Gender Code']),
        age: r['Age'] != null ? Number(r['Age']) || null : null,
        drug: safe(r['Primary Drug Of Choice'] || r['Primary Drug Of Choice ']),
        ref: safe(r['Referral Source']),
        dtype: safe(r['Discharge Type']),
        los: r['Length Of Stay'] != null ? Number(r['Length Of Stay']) || null : null,
        name: safe(r['Patient Name']),
      }));

      const oppRows = opps.recordset.map(r => {
        const oid = r.opportunity_id;
        return {
          id: oid == null ? '' : typeof oid === 'number' ? String(Math.round(oid)) : safe(oid),
          co: fmtMmDd(r.created_on),
          adm: fmtMmDd(r.admission_date),
          outcome: safe(r.outcome),
          stage: safe(r.stage),
          loc: safe(r.level_of_care),
          ins: safe(r['insurance provider']),
          ref: safe(r['referral name']),
          lost_r: safe(r['lost reason']),
          aband_r: safe(r['abandoned reason']),
          name: safe(r['patient name']),
        };
      });

      const timelineRows = timeline.recordset.map(r => {
        const oid = r.opportunity_id;
        const ad = r.activity_date;
        return {
          oid: oid == null ? '' : typeof oid === 'number' ? String(Math.round(oid)) : safe(oid),
          date: fmtMmDdTime(ad),
          subject: safe(r.task_subject),
          type: safe(r.type),
          by: safe(r.created_by_name),
          wf: safe(r.workflow_status),
          text: safe(r.text),
          sortKey: ad instanceof Date && !isNaN(ad.getTime()) ? ad.getTime() / 1000 : 0,
        };
      });

      const authRows = auth.recordset.map(r => ({
        adm: fmtMmDd(r.admission_date),
        nrd: fmtMmDd(r.next_review_date),
        code: safe(r.authorization_code),
        au: Math.round(num(r.authorized_units) * 10) / 10,
        bu: Math.round(num(r.billed_units_total) * 10) / 10,
        ins: safe(r.insurance_provider),
        reviewer: safe(r.ur_reviewer),
        patient: safe(r.patient_name),
        facility: safe(r.service_facility),
      }));

      const opsRows = admitted.recordset.map(r => {
        const ad = r['Admission Date'];
        const at = r['Admission Time'];
        let hr = -1;
        if (at instanceof Date && !isNaN(at.getTime())) hr = at.getHours();
        let dow = -1;
        if (ad instanceof Date && !isNaN(ad.getTime())) dow = (ad.getDay()) % 7;
        return {
          date: fmtMmDd(ad),
          hour: hr,
          dow,
          rep: safe(r['Admissions Rep']),
          therapist: safe(r['Assigned Therapist']),
          ins: safe(r['Insurance Name']),
          loc: safe(r['Admission Level Of Care']),
          name: safe(r['Patient Name']),
        };
      });

      const gnotesRows = gnotes.recordset.map(r => ({
        date: fmtMmDd(r.session_date),
        title: safe(r.group_title),
        status: safe(r.status),
        mins: Math.round(num(r.length_time)),
      }));

      const crmTaskRows = crmTask.recordset.map(r => {
        const ad = r.activity_date;
        return {
          id: safe(r.id),
          aid: safe(r.Associated_id || r.associated_with_id),
          assoc: safe(r.associated_with),
          subject: safe(r.task_subject),
          type: safe(r.type),
          task_type: safe(r.task_type),
          status: safe(r.task_status),
          created_by: safe(r.created_by_name),
          assigned: safe(r.assigned_to_name),
          text: safe(r.text),
          activity: fmtMmDdTime(ad),
          due: fmtMmDdTime(r.task_due_date),
          reminder: fmtMmDdTime(r.reminder_date_time),
          sortKey: ad instanceof Date && !isNaN(ad.getTime()) ? ad.getTime() / 1000 : 0,
        };
      });

      const referralRows = referrals.recordset.map(r => {
        const rid = r.referral_id || r.id;
        return {
          id: rid == null ? '' : typeof rid === 'number' ? String(Math.round(rid)) : safe(rid),
          co: fmtMmDd(r.created_on),
          name: safe(r['referral name'] || r.name),
          type: safe(r['referral type']),
          stage: safe(r['referral source stage']),
          owner: safe(r.referral_source_owner),
          city: safe(r['referral source city']),
          state: safe(r['referral source state']),
        };
      });

      return {
        jsonBody: {
          billing: billingRows,
          census: censusRows,
          opps: oppRows,
          timeline: timelineRows,
          auth: authRows,
          ops: opsRows,
          gnotes: gnotesRows,
          crmTasks: crmTaskRows,
          referrals: referralRows,
          meta: { refreshed_at: new Date().toISOString() },
        },
      };
    } catch (err) {
      context.error('dashboard-combined:', err.message);
      return { status: 500, jsonBody: { error: err.message } };
    }
  },
});

// ── Report data endpoint (for field explorer / general tabs) ────────────────

app.http('dashboard-report-data', {
  methods: ['GET'],
  authLevel: 'anonymous',
  route: 'dashboard/report-data',
  handler: async (request, context) => {
    const SHEETS = {
      'Census': 'vw_excel_census',
      'Census Active': 'vw_excel_census_active',
      'Census_Admitted': 'vw_excel_census_admitted',
      'Census_Discharge': 'vw_excel_census_discharge',
      'GroupNotes': 'vw_excel_group_notes',
      'Incident Report': 'vw_excel_incident_report',
      'Opportunities': 'vw_excel_opportunities',
      'Opportunities Active': 'vw_excel_opportunities_active',
      'Opportunities by Created Date': 'vw_excel_opportunities_by_created_date',
      'Patients': 'vw_excel_patients',
      'Payment Report Deposit Date': 'vw_excel_payment_report_deposit_date',
      'Payment Report Payment Date': 'vw_excel_payment_report_payment_date',
      'Referral Active': 'vw_excel_referral_active',
      'Report Auth': 'vw_excel_report_auth',
      'Report Deleted Form': 'vw_excel_report_deleted_form',
      'Report Diagnois Changes': 'vw_excel_report_diagnosis_changes',
      'Report Form Modified': 'vw_excel_report_form_modified',
      'Report Program Change': 'vw_excel_report_program_change',
      'Report UR Changes': 'vw_excel_report_ur_changes',
      'Users': 'vw_excel_users',
      'CRM Task': 'vw_excel_crm_task',
      'Timeline': 'vw_excel_timeline',
    };

    try {
      const out = {};
      for (const [sheetName, viewName] of Object.entries(SHEETS)) {
        try {
          const result = await query(`SELECT * FROM dbo.${viewName}`);
          const cols = result.recordset.columns
            ? Object.keys(result.recordset.columns)
            : result.recordset.length > 0 ? Object.keys(result.recordset[0]) : [];
          const rows = result.recordset.map(row =>
            cols.map(c => {
              const v = row[c];
              if (v instanceof Date && !isNaN(v.getTime())) {
                return `${String(v.getMonth() + 1).padStart(2, '0')}/${String(v.getDate()).padStart(2, '0')}/${v.getFullYear()}`;
              }
              return v == null ? '' : String(v);
            })
          );
          out[sheetName] = { columns: cols, rows };
        } catch (e) {
          context.warn(`Skipping ${viewName}: ${e.message}`);
        }
      }
      return { jsonBody: out };
    } catch (err) {
      context.error('dashboard-report-data:', err.message);
      return { status: 500, jsonBody: { error: err.message } };
    }
  },
});
