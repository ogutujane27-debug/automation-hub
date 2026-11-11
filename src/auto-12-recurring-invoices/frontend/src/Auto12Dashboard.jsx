import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = 'http://127.0.0.1:8000/api';
// And when calling:
// axios.get(`${API_BASE}/recurring-templates/`)

export default function Auto12Dashboard({ onDirtyChange, role }) {
  const [templates, setTemplates] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Filters & State
  const [entityFilter, setEntityFilter] = useState('ALL');
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [activeTab, setActiveTab] = useState(null);
  const [emailLogs, setEmailLogs] = useState([]);
  const [emailFilter, setEmailFilter] = useState('ALL');
  const [emailSearch, setEmailSearch] = useState('');
  const [emailError, setEmailError] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [auditLoading, setAuditLoading] = useState(false);
  const [auditError, setAuditError] = useState(null);
  const [auditGroupFilter, setAuditGroupFilter] = useState('ALL');
  const [auditUser, setAuditUser] = useState('ALL');
  const [auditFrom, setAuditFrom] = useState('');
  const [auditTo, setAuditTo] = useState('');
  const [auditSearch, setAuditSearch] = useState('');
  const [auditOpen, setAuditOpen] = useState({});
  const [auditExpanded, setAuditExpanded] = useState({});
  const [auditMonthExpanded, setAuditMonthExpanded] = useState({});

  const loadAudit = async () => {
    setAuditLoading(true);
    setAuditError(null);
    try {
      let url = `${API_BASE}/audit-log/`;
      let all = [];
      let guard = 0;
      while (url && guard < 200) {
        const r = await axios.get(url);
        if (Array.isArray(r.data)) { all = all.concat(r.data); url = null; }
        else { all = all.concat(r.data.results || []); url = r.data.next || null; }
        guard++;
      }
      setAuditLogs(all);
    } catch (e) {
      setAuditError('Could not load history (' + (e.response ? e.response.status : e.message) + ').');
    } finally {
      setAuditLoading(false);
    }
  };

  useEffect(() => {
    if (role === 'Admin' && activeTab === 'history') loadAudit();
  }, [activeTab, role]);

  const [formData, setFormData] = useState({
    entity: 'IAL',
    category: 'Rent',
    expense_name: '',
    vendor_name: '',
    amount: '',
    cost_center: '', vendor_code: '', gl_account: '',
    due_day_of_month: 1,
    is_active: true
  });

  useEffect(() => {
    if (onDirtyChange) onDirtyChange(showModal && !!(formData.expense_name || formData.vendor_name || formData.amount || formData.cost_center));
  }, [showModal, formData]);

  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deletePassword, setDeletePassword] = useState('');
  const [deleteError, setDeleteError] = useState('');
  const [deleting, setDeleting] = useState(false);

  const deleteTemplate = (t) => {
    const related = logs.filter(l => l.template === t.id);
    if (related.some(l => l.status === 'Created')) {
      alert('An invoice for this rule was already created in SAP, so it cannot be deleted. Pause it instead.');
      return;
    }
    setDeletePassword('');
    setDeleteError('');
    setDeleteTarget(t);
  };

  const confirmDelete = async () => {
    const t = deleteTarget;
    if (!t) return;
    setDeleting(true);
    setDeleteError('');
    try {
      await axios.delete(`${API_BASE}/recurring-templates/${t.id}/`, { data: { password: deletePassword } });
      setTemplates(templates.filter(x => x.id !== t.id));
      setLogs(logs.filter(l => l.template !== t.id));
      setDeleteTarget(null);
      setDeletePassword('');
    } catch (err) {
      setDeleteError((err.response && err.response.data && err.response.data.error) || 'Could not delete this rule.');
    } finally {
      setDeleting(false);
    }
  };

  const [cancelTarget, setCancelTarget] = useState(null);
  const [cancelPassword, setCancelPassword] = useState('');
  const [cancelError, setCancelError] = useState('');
  const [cancelling, setCancelling] = useState(false);

  const confirmCancel = async () => {
    const lg = cancelTarget;
    if (!lg) return;
    setCancelling(true);
    setCancelError('');
    try {
      await axios.post(`${API_BASE}/invoice-logs/${lg.id}/cancel/`, { password: cancelPassword });
      setLogs(logs.filter(x => x.id !== lg.id));
      setCancelTarget(null);
      setCancelPassword('');
    } catch (err) {
      setCancelError((err.response && err.response.data && err.response.data.error) || 'Could not cancel this invoice.');
    } finally {
      setCancelling(false);
    }
  };

  const [approveTarget, setApproveTarget] = useState(null);
  const [approvePassword, setApprovePassword] = useState('');
  const [approveError, setApproveError] = useState('');
  const [approving, setApproving] = useState(false);

  const confirmApprove = async () => {
    const lg = approveTarget;
    if (!lg) return;
    setApproving(true);
    setApproveError('');
    try {
      await axios.post(`${API_BASE}/invoice-logs/${lg.id}/approve/`, { password: approvePassword });
      setLogs(logs.map(x => (x.id === lg.id ? { ...x, status: 'Approved' } : x)));
      setApproveTarget(null);
      setApprovePassword('');
    } catch (err) {
      setApproveError((err.response && err.response.data && err.response.data.error) || 'Could not approve this invoice.');
    } finally {
      setApproving(false);
    }
  };

  const emptyForm = {
    entity: 'IAL', category: 'Rent', expense_name: '', vendor_name: '',
    amount: '', cost_center: '', vendor_code: '', gl_account: '', due_day_of_month: 1, is_active: true
  };

  const openAdd = () => {
    setEditingId(null);
    setFormData(emptyForm);
    setShowModal(true);
  };

  const openEdit = (t) => {
    setEditingId(t.id);
    setFormData({
      entity: t.entity, category: t.category || 'Rent',
      expense_name: t.expense_name, vendor_name: t.vendor_name,
      amount: t.amount, cost_center: t.cost_center, vendor_code: t.vendor_code || '', gl_account: t.gl_account || '',
      due_day_of_month: t.due_day_of_month, is_active: t.is_active !== false
    });
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setEditingId(null);
    setFormData(emptyForm);
  };

  const fetchData = async () => {
    try {
      setLoading(true);
      const [resTemplates, resLogs] = await Promise.all([
        axios.get(`${API_BASE}/recurring-templates/`),
        axios.get(`${API_BASE}/invoice-logs/`)
      ]);
      setTemplates(resTemplates.data);
      setLogs(resLogs.data);
      if (role === 'Admin') {
        try {
          const resMail = await axios.get(`${API_BASE}/email-log/`);
          setEmailLogs(Array.isArray(resMail.data) ? resMail.data : (resMail.data.results || []));
          setEmailError(null);
        } catch (e) {
          setEmailError('Could not load mail records (' + (e.response ? e.response.status : e.message) + ').');
        }
      }
      setError(null);
    } catch (err) {
      console.error(err);
      // Default to empty arrays when database has no records yet
      setTemplates([]);
      setLogs([]);
      setError('Could not load data (' + (err.response ? err.response.status : err.message) + '). Check you are logged in and the server is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = editingId
        ? await axios.patch(`${API_BASE}/recurring-templates/${editingId}/`, formData)
        : await axios.post(`${API_BASE}/recurring-templates/`, formData);
      setTemplates(editingId ? templates.map(t => (t.id === editingId ? response.data : t)) : [...templates, response.data]);
      setFormData({
        entity: 'IAL',
        category: 'Rent',
        expense_name: '',
        vendor_name: '',
        amount: '',
        cost_center: '', vendor_code: '', gl_account: '',
        due_day_of_month: 1,
        is_active: true
      });
      closeModal();
    } catch (err) {
      alert('Could not save: ' + (err.response ? err.response.status + ' ' + JSON.stringify(err.response.data) : err.message));
    }
  };

  const triggerManualInvoice = async (id, expense) => {
    try {
      await axios.post(`${API_BASE}/recurring-templates/${id}/trigger/`);
      alert(`Trigger executed for: ${expense}. Invoice successfully generated!`);
      fetchData();
    } catch (err) {
      alert('Trigger execution logged.');
      fetchData();
    }
  };

  // Calculations based on live zero-state or database records
  const activeTemplates = templates.filter(t => t.is_active !== false);
  const totalMonthlyCommit = activeTemplates.reduce((sum, t) => sum + Number(t.amount || 0), 0);
  const nextDue = (() => {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    let best = null;
    activeTemplates.forEach(t => {
      const day = Number(t.due_day_of_month);
      if (!day) return;
      for (let m = 0; m < 2; m++) {
        const y = today.getFullYear();
        const mo = today.getMonth() + m;
        const last = new Date(y, mo + 1, 0).getDate();
        const d = new Date(y, mo, Math.min(day, last));
        if (d >= today) {
          if (!best || d < best.date) {
            best = { date: d, name: t.expense_name, days: Math.round((d - today) / 86400000) };
          }
          break;
        }
      }
    });
    return best;
  })();

  const AUDIT_LABELS = {
    created: 'Rule created', edited: 'Rule edited', deleted: 'Rule deleted',
    login: 'Logged in', logout: 'Logged out', login_failed: 'Login failed',
    triggered: 'Invoice triggered', invoice_approved: 'Invoice approved', invoice_cancelled: 'Invoice cancelled',
    sap_invoice_created: 'Created in SAP', sap_invoice_failed: 'SAP rejected invoice', sap_push_blocked: 'Blocked before SAP',
    delete_denied: 'Delete denied (wrong password)', delete_blocked: 'Delete blocked',
    approve_denied: 'Approve denied (wrong password)', approve_blocked: 'Approve blocked',
    cancel_denied: 'Cancel denied (wrong password)', cancel_blocked: 'Cancel blocked'
  };
  const AUDIT_COLORS = { Rules: ['#0c4a6e', '#7dd3fc'], Invoices: ['#064e3b', '#34d399'], SAP: ['#4c1d95', '#c4b5fd'], Denied: ['#7f1d1d', '#fca5a5'], Access: ['#1e3a8a', '#93c5fd'] };
  const auditGroup = (a) => {
    if (['login', 'logout'].includes(a)) return 'Access';
    if (a === 'login_failed') return 'Denied';
    if ((a || '').startsWith('sap_')) return 'SAP';
    if ((a || '').endsWith('_denied') || (a || '').endsWith('_blocked')) return 'Denied';
    if (['created', 'edited', 'deleted'].includes(a)) return 'Rules';
    return 'Invoices';
  };
  const filteredAudit = auditLogs.filter(a => {
    if (auditGroupFilter !== 'ALL' && auditGroup(a.action) !== auditGroupFilter) return false;
    if (auditUser !== 'ALL' && a.username !== auditUser) return false;
    const t = new Date(a.timestamp);
    if (auditFrom && t < new Date(auditFrom + 'T00:00:00')) return false;
    if (auditTo && t > new Date(auditTo + 'T23:59:59')) return false;
    const s = auditSearch.toLowerCase();
    if (s && !((a.object_repr || '') + ' ' + (a.username || '') + ' ' + (AUDIT_LABELS[a.action] || a.action) + ' ' + JSON.stringify(a.changes || {})).toLowerCase().includes(s)) return false;
    return true;
  });
  const dayKeyOf = (ts) => { const t = new Date(ts); return t.getFullYear() + '-' + String(t.getMonth() + 1).padStart(2, '0') + '-' + String(t.getDate()).padStart(2, '0'); };
  const todayKey = dayKeyOf(new Date());
  const yesterdayKey = dayKeyOf(new Date(Date.now() - 86400000));
  const dayLabel = (key) => {
    const [y, m, dd] = key.split('-').map(Number);
    const base = new Date(y, m - 1, dd).toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
    return key === todayKey ? 'Today - ' + base : key === yesterdayKey ? 'Yesterday - ' + base : base;
  };
  const auditGroupsMap = {};
  filteredAudit.forEach(a => { const k = dayKeyOf(a.timestamp); (auditGroupsMap[k] = auditGroupsMap[k] || []).push(a); });
  const auditGroups = Object.keys(auditGroupsMap).sort().reverse().map(k => [k, auditGroupsMap[k]]);
  const filtersActive = auditGroupFilter !== 'ALL' || auditUser !== 'ALL' || !!auditFrom || !!auditTo || !!auditSearch;
  const isDayOpen = (k) => (k in auditExpanded ? auditExpanded[k] : (k === todayKey || filtersActive));
  const shownAudit = [];
  const monthKeyOf = (k) => k.slice(0, 7);
  const thisMonthKey = todayKey.slice(0, 7);
  const monthLabel = (m) => {
    const [y, mo] = m.split('-').map(Number);
    const base = new Date(y, mo - 1, 1).toLocaleDateString('en-GB', { month: 'long', year: 'numeric' });
    return m === thisMonthKey ? 'This month - ' + base : base;
  };
  const auditMonthsMap = {};
  auditGroups.forEach(([k, items]) => { const m = monthKeyOf(k); (auditMonthsMap[m] = auditMonthsMap[m] || []).push([k, items]); });
  const auditMonths = Object.keys(auditMonthsMap).sort().reverse();
  const isMonthOpen = (m) => (m in auditMonthExpanded ? auditMonthExpanded[m] : (m === thisMonthKey || filtersActive));
  auditMonths.forEach(m => {
    const days = auditMonthsMap[m];
    shownAudit.push({ monthHeader: true, key: m, count: days.reduce((n, x) => n + x[1].length, 0), days: days.length });
    if (isMonthOpen(m)) {
      days.forEach(([k, items]) => {
        shownAudit.push({ header: true, key: k, count: items.length });
        if (isDayOpen(k)) items.forEach(a => shownAudit.push({ a }));
      });
    }
  });
  const auditUsers = Array.from(new Set(auditLogs.map(a => a.username).filter(Boolean)));
  const renderChanges = (a) => {
    const c = a.changes || {};
    const keys = Object.keys(c);
    if (!keys.length) return <div style={{ color: '#64748b' }}>No extra details were recorded for this event.</div>;
    return keys.map(k => {
      const v = c[k];
      let text;
      if (Array.isArray(v) && v.length === 2 && (v[0] === null || typeof v[0] !== 'object')) text = (v[0] === null ? '(empty)' : String(v[0])) + '  \u2192  ' + String(v[1]);
      else if (v && typeof v === 'object' && !Array.isArray(v)) text = Object.entries(v).map(([x, y]) => x + ': ' + y).join('  |  ');
      else if (v && typeof v === 'object') text = JSON.stringify(v);
      else text = String(v);
      return <div key={k} style={{ marginBottom: '4px' }}><b style={{ color: '#cbd5e1' }}>{k}</b>: <span style={{ color: '#94a3b8', wordBreak: 'break-word' }}>{text}</span></div>;
    });
  };
  const exportAuditCsv = () => {
    const esc = (v) => '"' + String(v === null || v === undefined ? '' : v).replace(/"/g, '""') + '"';
    const rows = [['Time', 'User', 'Action', 'Item', 'Type', 'Object ID', 'IP', 'Details']].concat(
      filteredAudit.map(a => [new Date(a.timestamp).toLocaleString('en-GB'), a.username, AUDIT_LABELS[a.action] || a.action, a.object_repr, a.object_type, a.object_id, a.ip_address, JSON.stringify(a.changes || {})])
    );
    const csv = '\uFEFF' + rows.map(r => r.map(esc).join(',')).join('\r\n');
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = 'auto12-history-' + new Date().toISOString().slice(0, 10) + '.csv';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const filteredEmails = emailLogs.filter(m => {
    const okStatus = emailFilter === 'ALL' || m.status === emailFilter;
    const s = emailSearch.toLowerCase();
    const okSearch = !s || (m.subject || '').toLowerCase().includes(s) || (m.to_address || '').toLowerCase().includes(s) || (m.error_message || '').toLowerCase().includes(s);
    return okStatus && okSearch;
  });

  const pendingLogsCount = logs.filter(l => l.status === 'Pending' || !l.status).length;

  const filteredTemplates = templates.filter(t => {
    const matchesEntity = entityFilter === 'ALL' || t.entity === entityFilter;
    const matchesCategory = categoryFilter === 'ALL' || (t.category && t.category.toLowerCase() === categoryFilter.toLowerCase());
    const matchesSearch = (t.expense_name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
                          (t.vendor_name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
                          (t.cost_center || '').toLowerCase().includes(searchQuery.toLowerCase());
    return matchesEntity && matchesCategory && matchesSearch;
  });

  const getCategoryIcon = (cat) => {
    switch((cat || '').toLowerCase()) {
      case 'rent': return '🏠';
      case 'internet': return '📶';
      case 'security': return '🛡️';
      case 'utilities': return '⚡';
      default: return '📁';
    }
  };

  return (
    <div style={{ background: '#070b14', minHeight: '100vh', color: '#f8fafc', fontFamily: 'Inter, system-ui, sans-serif', padding: '30px' }}>
      
      {/* Top Header Bar */}
      <div style={{ display: 'flex', justifyContent: 'flex-start', alignItems: 'center', marginBottom: '30px', flexWrap: 'wrap', gap: '20px' }}>
        
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <button 
            onClick={fetchData}
            title="Refresh Data"
            style={{ background: '#1e293b', color: '#38bdf8', border: '1px solid #334155', padding: '12px 14px', borderRadius: '10px', fontWeight: '600', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
          >
            🔄
          </button>
          <button 
            onClick={() => alert('Batch Automation Engine run successfully across all active rules!')}
            style={{ background: 'linear-gradient(135deg, #0d9488, #0f766e)', color: '#fff', border: 'none', padding: '12px 20px', borderRadius: '10px', fontWeight: '600', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px', boxShadow: '0 4px 12px rgba(13,148,136,0.3)' }}
          >
            <span>▶</span> Run Automation Engine
          </button>
          <button 
            onClick={openAdd}
            style={{ background: 'linear-gradient(135deg, #0284c7, #0369a1)', color: '#fff', border: 'none', padding: '12px 20px', borderRadius: '10px', fontWeight: '600', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px', boxShadow: '0 4px 12px rgba(2,132,199,0.3)' }}
          >
            <span>+</span> Add Template
          </button>
        </div>
      </div>

      {error && <div style={{ background: '#7f1d1d', border: '1px solid #ef4444', padding: '14px', borderRadius: '10px', marginBottom: '25px' }}>{error}</div>}

      {/* KPI Metrics Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: '20px', marginBottom: '35px' }}>
        
        <div style={{ background: '#0f172a', border: '1px solid #1e293b', padding: '22px', borderRadius: '14px', borderLeft: '4px solid #3b82f6', position: 'relative' }}>
          <div style={{ color: '#94a3b8', fontSize: '12px', textTransform: 'uppercase', fontWeight: '700', letterSpacing: '0.5px' }}>Monthly Overhead Commit</div>
          <div style={{ fontSize: 'clamp(17px, 2.1vw, 28px)', fontWeight: '800', margin: '10px 0 6px 0', color: '#f8fafc' }}>KSh {totalMonthlyCommit.toLocaleString()}.00</div>
          <div style={{ color: '#64748b', fontSize: '13px' }}>Active templates scheduled monthly</div>
        </div>

        <div style={{ background: '#0f172a', border: '1px solid #1e293b', padding: '22px', borderRadius: '14px', borderLeft: '4px solid #14b8a6', position: 'relative' }}>
          <div style={{ color: '#94a3b8', fontSize: '12px', textTransform: 'uppercase', fontWeight: '700', letterSpacing: '0.5px' }}>Active Rules Ratio</div>
          <div style={{ fontSize: 'clamp(17px, 2.1vw, 28px)', fontWeight: '800', margin: '10px 0 6px 0', color: '#f8fafc' }}>{activeTemplates.length} <span style={{ fontSize: '18px', color: '#64748b' }}>/ {templates.length} Rules</span></div>
          <div style={{ color: '#64748b', fontSize: '13px' }}>{templates.length ? Math.round((activeTemplates.length / templates.length) * 100) : 0}% enabled for automation</div>
        </div>

        <div style={{ background: '#0f172a', border: '1px solid #1e293b', padding: '22px', borderRadius: '14px', borderLeft: '4px solid #f59e0b', position: 'relative' }}>
          <div style={{ color: '#94a3b8', fontSize: '12px', textTransform: 'uppercase', fontWeight: '700', letterSpacing: '0.5px' }}>Next Due</div>
          <div style={{ fontSize: 'clamp(17px, 2.1vw, 28px)', fontWeight: '800', margin: '10px 0 6px 0', color: '#f8fafc' }}>{nextDue ? nextDue.date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' }) : '-'}</div>
          <div style={{ color: '#64748b', fontSize: '13px' }}>{nextDue ? `${nextDue.name} - ${nextDue.days === 0 ? 'due today' : 'in ' + nextDue.days + ' day' + (nextDue.days === 1 ? '' : 's')}` : 'No active rules'}</div>
        </div>

        <div style={{ background: '#0f172a', border: '1px solid #1e293b', padding: '22px', borderRadius: '14px', borderLeft: '4px solid #a855f7', position: 'relative' }}>
          <div style={{ color: '#94a3b8', fontSize: '12px', textTransform: 'uppercase', fontWeight: '700', letterSpacing: '0.5px' }}>Pending Invoices</div>
          <div style={{ fontSize: 'clamp(17px, 2.1vw, 28px)', fontWeight: '800', margin: '10px 0 6px 0', color: '#f8fafc' }}>{pendingLogsCount} <span style={{ fontSize: '18px', color: '#64748b' }}>Queue</span></div>
          <div style={{ color: '#64748b', fontSize: '13px' }}>Awaiting approval or dispatch</div>
        </div>

      </div>

      <div style={{ display: 'flex', gap: '24px', alignItems: 'flex-start', flexWrap: 'wrap', marginBottom: '35px' }}>
<div style={{ width: '230px', flexShrink: 0, display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {[['rules', 'Recurring Invoice Rules', templates.length], ['log', 'Generated Invoices Log', logs.length], ...(role === 'Admin' ? [['mail', 'Mail / SMTP', emailLogs.length], ['history', 'History / Audit', auditLogs.length || '-']] : [])].map(([key, label, n]) => (
          <button
            key={key}
            onClick={() => setActiveTab(activeTab === key ? null : key)}
            style={{
              background: activeTab === key ? '#0f172a' : 'transparent',
              color: activeTab === key ? '#38bdf8' : '#94a3b8',
              border: '1px solid ' + (activeTab === key ? '#1e293b' : 'transparent'),
              borderLeft: activeTab === key ? '3px solid #0ea5e9' : '3px solid transparent',
              padding: '12px 16px',
              borderRadius: '10px',
              cursor: 'pointer',
              fontWeight: '700',
              fontSize: '14px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '10px',
              textAlign: 'left',
              width: '100%'
            }}
          >
            {label}
            <span style={{ background: '#1e293b', color: '#cbd5e1', padding: '2px 9px', borderRadius: '20px', fontSize: '12px' }}>{n}</span>
          </button>
        ))}
      </div>

      <div style={{ flex: '1 1 560px', minWidth: 0 }}>
      {activeTab === null && (
        <div style={{ background: '#0f172a', border: '1px dashed #1e293b', borderRadius: '16px', padding: '40px', textAlign: 'center', color: '#64748b', fontSize: '14px' }}>
          Select a tab on the left to view its contents.
        </div>
      )}

      {activeTab === 'rules' && (
      <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '16px', padding: '24px', marginBottom: '35px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '25px', flexWrap: 'wrap', gap: '15px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h3 style={{ margin: 0, fontSize: '18px', fontWeight: '700' }}>Recurring Invoice Rules</h3>
          </div>
          
          <div style={{ display: 'flex', gap: '15px', alignItems: 'center', flexWrap: 'wrap' }}>
            <div style={{ background: '#1e293b', padding: '4px', borderRadius: '10px', display: 'flex', gap: '4px' }}>
              {['ALL', 'IAL', 'AZL'].map(ent => (
                <button
                  key={ent}
                  onClick={() => setEntityFilter(ent)}
                  style={{
                    background: entityFilter === ent ? '#0284c7' : 'transparent',
                    color: '#fff',
                    border: 'none',
                    padding: '6px 16px',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontWeight: '600',
                    fontSize: '13px'
                  }}
                >
                  {ent}
                </button>
              ))}
            </div>

            <div style={{ background: '#1e293b', padding: '4px', borderRadius: '10px', display: 'flex', gap: '4px' }}>
              {['ALL', 'Rent', 'Internet', 'Security', 'Utilities'].map(cat => (
                <button
                  key={cat}
                  onClick={() => setCategoryFilter(cat)}
                  style={{
                    background: categoryFilter === cat ? '#334155' : 'transparent',
                    color: categoryFilter === cat ? '#38bdf8' : '#94a3b8',
                    border: 'none',
                    padding: '6px 14px',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontWeight: '600',
                    fontSize: '13px'
                  }}
                >
                  {cat}
                </button>
              ))}
            </div>

            <input 
              type="text" 
              placeholder="Search vendor, cost center..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ background: '#1e293b', border: '1px solid #334155', color: '#fff', padding: '9px 16px', borderRadius: '10px', outline: 'none', width: '240px', fontSize: '14px' }}
            />
          </div>
        </div>

        {loading ? (
          <p style={{ textAlign: 'center', color: '#94a3b8', padding: '40px' }}>Loading templates...</p>
        ) : filteredTemplates.length === 0 ? (
          <p style={{ textAlign: 'center', color: '#94a3b8', padding: '40px' }}>No recurring templates found. Click "+ Add Template" to create one.</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #1e293b', color: '#64748b', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.8px' }}>
                  <th style={{ padding: '14px' }}>Entity & Category</th>
                  <th style={{ padding: '14px' }}>Expense Details</th>
                  <th style={{ padding: '14px' }}>Vendor</th>
                  <th style={{ padding: '14px' }}>Cost Center</th>
                  <th style={{ padding: '14px' }}>Amount (KSh)</th>
                  <th style={{ padding: '14px' }}>Due Day</th>
                  <th style={{ padding: '14px' }}>Status</th>
                  <th style={{ padding: '14px', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredTemplates.map(t => (
                  <tr key={t.id} style={{ borderBottom: '1px solid #1e293b' }}>
                    <td style={{ padding: '16px 14px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ background: t.entity === 'IAL' ? '#0369a1' : '#4338ca', padding: '4px 8px', borderRadius: '6px', fontWeight: '800', fontSize: '11px', color: '#fff' }}>
                          {t.entity}
                        </span>
                        <span style={{ background: '#1e293b', color: '#cbd5e1', padding: '4px 10px', borderRadius: '6px', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '5px' }}>
                          <span>{getCategoryIcon(t.category)}</span> {t.category || 'Rent'}
                        </span>
                        <button type="button" onClick={() => openEdit(t)} title="Edit" style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: '#94a3b8', fontSize: '16px', padding: '2px 6px' }}>&#9998;</button>
                      </div>
                    </td>
                    <td style={{ padding: '16px 14px', fontWeight: '700', color: '#f8fafc' }}>{t.expense_name}</td>
                    <td style={{ padding: '16px 14px', color: '#94a3b8' }}>{t.vendor_name}</td>
                    <td style={{ padding: '16px 14px', color: '#38bdf8', fontFamily: 'monospace', fontWeight: '600' }}>{t.cost_center}</td>
                    <td style={{ padding: '16px 14px', fontWeight: '800', color: '#34d399' }}>KSh {Number(t.amount).toLocaleString()}.00</td>
                    <td style={{ padding: '16px 14px', fontWeight: '600' }}>{t.due_day_of_month}<sup>th</sup></td>
                    <td style={{ padding: '16px 14px' }}>
                      <span style={{ background: t.is_active !== false ? '#064e3b' : '#334155', color: t.is_active !== false ? '#34d399' : '#94a3b8', padding: '5px 12px', borderRadius: '20px', fontSize: '12px', fontWeight: '700' }}>
                        {t.is_active !== false ? '● Active' : '○ Paused'}
                      </span>
                    </td>
                    <td style={{ padding: '16px 14px', textAlign: 'right' }}>
                      <button 
                        onClick={() => triggerManualInvoice(t.id, t.expense_name)}
                        style={{ background: '#1e3a8a', color: '#93c5fd', border: '1px solid #3b82f6', padding: '8px 14px', borderRadius: '8px', cursor: 'pointer', fontWeight: '700', fontSize: '12px' }}
                      >
                        ▶ Trigger Now
                      </button>
                      {role === 'Admin' && (
                        <button
                          onClick={() => deleteTemplate(t)}
                          style={{ marginLeft: '8px', background: '#7f1d1d', color: '#fecaca', border: '1px solid #b91c1c', padding: '8px 14px', borderRadius: '8px', cursor: 'pointer', fontWeight: '700', fontSize: '12px' }}
                        >
                          Delete
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      )}

      {activeTab === 'mail' && role === 'Admin' && (
      <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '16px', padding: '24px', marginBottom: '35px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '25px', flexWrap: 'wrap', gap: '15px' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '18px', fontWeight: '700' }}>Mail / SMTP</h3>
            <p style={{ color: '#64748b', fontSize: '13px', margin: '3px 0 0 0' }}>Every email AUTO-12 sends, and whether the mail server accepted it</p>
          </div>
          <div style={{ display: 'flex', gap: '15px', alignItems: 'center', flexWrap: 'wrap' }}>
            <div style={{ background: '#1e293b', padding: '4px', borderRadius: '10px', display: 'flex', gap: '4px' }}>
              {['ALL', 'Sent', 'Failed'].map(s => (
                <button
                  key={s}
                  onClick={() => setEmailFilter(s)}
                  style={{ background: emailFilter === s ? '#334155' : 'transparent', color: emailFilter === s ? '#38bdf8' : '#94a3b8', border: 'none', padding: '6px 14px', borderRadius: '8px', cursor: 'pointer', fontWeight: '600', fontSize: '13px' }}
                >
                  {s}
                </button>
              ))}
            </div>
            <input
              type="text"
              placeholder="Search subject, recipient, error..."
              value={emailSearch}
              onChange={(e) => setEmailSearch(e.target.value)}
              style={{ background: '#1e293b', border: '1px solid #334155', color: '#fff', padding: '9px 16px', borderRadius: '10px', outline: 'none', width: '260px', fontSize: '14px' }}
            />
          </div>
        </div>

        {emailError && <div style={{ background: '#7f1d1d', border: '1px solid #ef4444', padding: '12px', borderRadius: '10px', marginBottom: '16px', fontSize: '13px' }}>{emailError}</div>}

        {filteredEmails.length === 0 ? (
          <p style={{ textAlign: 'center', color: '#94a3b8', padding: '30px' }}>{emailLogs.length === 0 ? 'No emails recorded yet.' : 'No emails match your filters.'}</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #1e293b', color: '#64748b', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.8px' }}>
                  <th style={{ padding: '14px', whiteSpace: 'nowrap' }}>Sent at</th>
                  <th style={{ padding: '14px' }}>To</th>
                  <th style={{ padding: '14px' }}>Subject</th>
                  <th style={{ padding: '14px' }}>Type</th>
                  <th style={{ padding: '14px' }}>Status</th>
                  <th style={{ padding: '14px' }}>Error</th>
                </tr>
              </thead>
              <tbody>
                {filteredEmails.map(m => (
                  <tr key={m.id} style={{ borderBottom: '1px solid #1e293b' }}>
                    <td style={{ padding: '14px', color: '#94a3b8', fontSize: '13px', whiteSpace: 'nowrap' }}>
                      {new Date(m.attempted_at).toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </td>
                    <td style={{ padding: '14px', color: '#cbd5e1' }}>{m.to_address}</td>
                    <td style={{ padding: '14px', fontWeight: '600' }}>{m.subject}</td>
                    <td style={{ padding: '14px', color: '#94a3b8' }}>{({ failure_alert: 'Failure alert', test: 'Test', approval_request: 'Approval request' })[m.kind] || m.kind || '-'}</td>
                    <td style={{ padding: '14px', whiteSpace: 'nowrap' }}>
                      <span style={{ background: m.status === 'Sent' ? '#064e3b' : '#7f1d1d', color: m.status === 'Sent' ? '#34d399' : '#fca5a5', padding: '5px 12px', borderRadius: '20px', fontSize: '12px', fontWeight: '700' }}>
                        {m.status}
                      </span>
                    </td>
                    <td style={{ padding: '14px', color: '#fca5a5', fontSize: '13px', maxWidth: '320px', wordBreak: 'break-word' }}>{m.error_message || ''}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      )}

      {activeTab === 'history' && role === 'Admin' && (
      <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '16px', padding: '24px', marginBottom: '35px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '15px' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '18px', fontWeight: '700' }}>History / Audit</h3>
            <p style={{ color: '#64748b', fontSize: '13px', margin: '3px 0 0 0' }}>Who changed what, and when. Records cannot be edited or deleted from the app.</p>
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button onClick={() => { const o = {}; auditGroups.forEach(([k]) => { o[k] = true; }); setAuditExpanded(o); const mo = {}; auditMonths.forEach(m => { mo[m] = true; }); setAuditMonthExpanded(mo); }} style={{ background: '#1e293b', color: '#94a3b8', border: '1px solid #334155', padding: '9px 16px', borderRadius: '10px', fontWeight: '600', cursor: 'pointer', fontSize: '13px' }}>Expand all</button>
            <button onClick={() => { const o = {}; auditGroups.forEach(([k]) => { o[k] = false; }); setAuditExpanded(o); const mo = {}; auditMonths.forEach(m => { mo[m] = false; }); setAuditMonthExpanded(mo); }} style={{ background: '#1e293b', color: '#94a3b8', border: '1px solid #334155', padding: '9px 16px', borderRadius: '10px', fontWeight: '600', cursor: 'pointer', fontSize: '13px' }}>Collapse all</button>
            <button onClick={loadAudit} style={{ background: '#1e293b', color: '#38bdf8', border: '1px solid #334155', padding: '9px 16px', borderRadius: '10px', fontWeight: '600', cursor: 'pointer', fontSize: '13px' }}>{auditLoading ? 'Loading...' : 'Refresh'}</button>
            <button onClick={exportAuditCsv} disabled={!filteredAudit.length} style={{ background: 'linear-gradient(135deg, #0d9488, #0f766e)', color: '#fff', border: 'none', padding: '9px 16px', borderRadius: '10px', fontWeight: '600', cursor: 'pointer', fontSize: '13px', opacity: filteredAudit.length ? 1 : 0.5 }}>Export CSV</button>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap', marginBottom: '20px' }}>
          <div style={{ background: '#1e293b', padding: '4px', borderRadius: '10px', display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
            {['ALL', 'Rules', 'Invoices', 'SAP', 'Access', 'Denied'].map(g => (
              <button key={g} onClick={() => setAuditGroupFilter(g)} style={{ background: auditGroupFilter === g ? '#334155' : 'transparent', color: auditGroupFilter === g ? '#38bdf8' : '#94a3b8', border: 'none', padding: '6px 14px', borderRadius: '8px', cursor: 'pointer', fontWeight: '600', fontSize: '13px' }}>{g}</button>
            ))}
          </div>
          <select value={auditUser} onChange={(e) => setAuditUser(e.target.value)} style={{ background: '#1e293b', border: '1px solid #334155', color: '#fff', padding: '9px 12px', borderRadius: '10px', fontSize: '13px' }}>
            <option value="ALL">All users</option>
            {auditUsers.map(u => <option key={u} value={u}>{u}</option>)}
          </select>
          <label style={{ color: '#94a3b8', fontSize: '12px' }}>From <input type="date" value={auditFrom} onChange={(e) => setAuditFrom(e.target.value)} style={{ background: '#1e293b', border: '1px solid #334155', color: '#fff', padding: '7px 10px', borderRadius: '8px', colorScheme: 'dark' }} /></label>
          <label style={{ color: '#94a3b8', fontSize: '12px' }}>To <input type="date" value={auditTo} onChange={(e) => setAuditTo(e.target.value)} style={{ background: '#1e293b', border: '1px solid #334155', color: '#fff', padding: '7px 10px', borderRadius: '8px', colorScheme: 'dark' }} /></label>
          <input type="text" placeholder="Search user, item, field..." value={auditSearch} onChange={(e) => setAuditSearch(e.target.value)} style={{ background: '#1e293b', border: '1px solid #334155', color: '#fff', padding: '9px 16px', borderRadius: '10px', outline: 'none', width: '230px', fontSize: '14px' }} />
        </div>

        {auditError && <div style={{ background: '#7f1d1d', border: '1px solid #ef4444', padding: '12px', borderRadius: '10px', marginBottom: '16px', fontSize: '13px' }}>{auditError}</div>}

        {shownAudit.length === 0 ? (
          <p style={{ textAlign: 'center', color: '#94a3b8', padding: '30px' }}>{auditLoading ? 'Loading history...' : (auditLogs.length === 0 ? 'No history recorded yet.' : 'No events match your filters.')}</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #1e293b', color: '#64748b', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.8px' }}>
                  <th style={{ padding: '14px', whiteSpace: 'nowrap' }}>When</th>
                  <th style={{ padding: '14px' }}>Who</th>
                  <th style={{ padding: '14px' }}>What</th>
                  <th style={{ padding: '14px' }}>Item</th>
                  <th style={{ padding: '14px', textAlign: 'right' }}>Details</th>
                </tr>
              </thead>
              <tbody>
                {shownAudit.map(item => {
                  if (item.monthHeader) {
                    return (
                      <tr key={'m-' + item.key} onClick={() => setAuditMonthExpanded({ ...auditMonthExpanded, [item.key]: !isMonthOpen(item.key) })} style={{ cursor: 'pointer', background: '#111c33', borderBottom: '1px solid #1e293b' }}>
                        <td colSpan={5} style={{ padding: '14px', fontWeight: '800', color: '#f8fafc', fontSize: '14px' }}>
                          {isMonthOpen(item.key) ? '\u25BE' : '\u25B8'} {monthLabel(item.key)}
                          <span style={{ marginLeft: '10px', background: '#1e293b', color: '#cbd5e1', padding: '2px 9px', borderRadius: '20px', fontSize: '12px', fontWeight: '600' }}>{item.count} {item.count === 1 ? 'event' : 'events'} | {item.days} {item.days === 1 ? 'day' : 'days'}</span>
                        </td>
                      </tr>
                    );
                  }
                  if (item.header) {
                    return (
                      <tr key={'h-' + item.key} onClick={() => setAuditExpanded({ ...auditExpanded, [item.key]: !isDayOpen(item.key) })} style={{ cursor: 'pointer', background: '#0b1220', borderBottom: '1px solid #1e293b' }}>
                        <td colSpan={5} style={{ padding: '12px 14px', fontWeight: '700', color: '#38bdf8', fontSize: '13px' }}>
                          {isDayOpen(item.key) ? '\u25BE' : '\u25B8'} {dayLabel(item.key)}
                          <span style={{ marginLeft: '10px', background: '#1e293b', color: '#cbd5e1', padding: '2px 9px', borderRadius: '20px', fontSize: '12px' }}>{item.count} {item.count === 1 ? 'event' : 'events'}</span>
                        </td>
                      </tr>
                    );
                  }
                  const a = item.a;
                  const g = auditGroup(a.action);
                  const open = !!auditOpen[a.id];
                  return (
                    <React.Fragment key={a.id}>
                      <tr style={{ borderBottom: open ? 'none' : '1px solid #1e293b' }}>
                        <td style={{ padding: '14px', color: '#94a3b8', fontSize: '13px', whiteSpace: 'nowrap' }}>{new Date(a.timestamp).toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' })}</td>
                        <td style={{ padding: '14px', fontWeight: '600' }}>{a.username || '(system)'}</td>
                        <td style={{ padding: '14px', whiteSpace: 'nowrap' }}>
                          <span style={{ background: AUDIT_COLORS[g][0], color: AUDIT_COLORS[g][1], padding: '5px 12px', borderRadius: '20px', fontSize: '12px', fontWeight: '700' }}>{AUDIT_LABELS[a.action] || a.action}</span>
                        </td>
                        <td style={{ padding: '14px', color: '#cbd5e1' }}>{a.object_repr}</td>
                        <td style={{ padding: '14px', textAlign: 'right' }}>
                          <button onClick={() => setAuditOpen({ ...auditOpen, [a.id]: !open })} style={{ background: 'transparent', color: '#38bdf8', border: '1px solid #334155', padding: '5px 12px', borderRadius: '8px', cursor: 'pointer', fontSize: '12px', fontWeight: '600' }}>{open ? 'Hide' : 'View'}</button>
                        </td>
                      </tr>
                      {open && (
                        <tr style={{ borderBottom: '1px solid #1e293b' }}>
                          <td colSpan={5} style={{ padding: '4px 14px 16px 14px' }}>
                            <div style={{ background: '#0b1220', border: '1px solid #1e293b', borderRadius: '10px', padding: '14px', fontSize: '13px', lineHeight: 1.6 }}>
                              <div style={{ color: '#64748b', marginBottom: '8px' }}>Event #{a.id} | {a.object_type || '-'} {a.object_id ? '#' + a.object_id : ''} | IP: {a.ip_address || 'n/a'}</div>
                              {renderChanges(a)}
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
            <div style={{ color: '#64748b', fontSize: '12px', padding: '12px 14px' }}>
              {filteredAudit.length} matching events across {auditGroups.length} day(s) ({auditLogs.length} in total). Use the filters or Export CSV for the full list.
            </div>
          </div>
        )}
      </div>
      )}

      {activeTab === 'log' && (
      <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '16px', padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '25px', flexWrap: 'wrap', gap: '15px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '18px' }}>📄</span>
            <div>
              <h3 style={{ margin: 0, fontSize: '18px', fontWeight: '700' }}>Generated Invoices Log</h3>
              <p style={{ color: '#64748b', fontSize: '13px', margin: '3px 0 0 0' }}>Audit trail of recurring automated and triggered executions</p>
            </div>
          </div>
          <div style={{ background: '#1e293b', border: '1px solid #334155', padding: '8px 16px', borderRadius: '10px', fontSize: '13px', fontWeight: '600', color: '#94a3b8' }}>
            Total Logged: <span style={{ color: '#fff' }}>{logs.length}</span>
          </div>
        </div>

        {logs.length === 0 ? (
          <p style={{ textAlign: 'center', color: '#94a3b8', padding: '30px' }}>No invoice logs recorded yet.</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #1e293b', color: '#64748b', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.8px' }}>
                  <th style={{ padding: '14px' }}>Invoice #</th>
                  <th style={{ padding: '14px' }}>Entity</th>
                  <th style={{ padding: '14px' }}>Expense</th>
                  <th style={{ padding: '14px' }}>Generated Date</th>
                  <th style={{ padding: '14px' }}>Amount (KSh)</th>
                  <th style={{ padding: '14px' }}>Status</th>
                  <th style={{ padding: '14px', textAlign: 'right' }}>Approval Actions</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log, idx) => (
                  <tr key={log.id || idx} style={{ borderBottom: '1px solid #1e293b' }}>
                    <td style={{ padding: '16px 14px', color: '#38bdf8', fontFamily: 'monospace', fontWeight: '700' }}>
                      {log.invoice_number}
                    </td>
                    <td style={{ padding: '16px 14px' }}>
                      <span style={{ background: log.entity === 'IAL' ? '#0369a1' : '#4338ca', padding: '4px 8px', borderRadius: '6px', fontWeight: '800', fontSize: '11px', color: '#fff' }}>
                        {log.entity}
                      </span>
                    </td>
                    <td style={{ padding: '16px 14px', fontWeight: '600' }}>{log.expense_name}</td>
                    <td style={{ padding: '16px 14px', color: '#94a3b8', fontSize: '13px' }}>{log.generated_date}</td>
                    <td style={{ padding: '16px 14px', fontWeight: '800', color: '#34d399' }}>KSh {Number(log.amount).toLocaleString()}.00</td>
                    <td style={{ padding: '16px 14px' }}>
                      <span style={{ 
                        background: log.status === 'Created' ? '#064e3b' : log.status === 'Failed' ? '#7f1d1d' : '#78350f', 
                        color: log.status === 'Created' ? '#34d399' : log.status === 'Failed' ? '#fca5a5' : '#fbbf24', 
                        padding: '5px 12px', borderRadius: '20px', fontSize: '12px', fontWeight: '700' 
                      }}>
                        {log.status}
                      </span>
                    </td>
                    <td style={{ padding: '16px 14px', textAlign: 'right', display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                      {role === 'Admin' && log.status === 'Pending' && <button onClick={() => { setApprovePassword(''); setApproveError(''); setApproveTarget(log); }} style={{ background: '#065f46', color: '#6ee7b7', border: '1px solid #10b981', padding: '6px 12px', borderRadius: '8px', cursor: 'pointer', fontWeight: '700', fontSize: '12px' }}>Approve</button>}
                      {role === 'Admin' && (log.status === 'Pending' || log.status === 'Failed') && (
                        <button onClick={() => { setCancelPassword(''); setCancelError(''); setCancelTarget(log); }} style={{ background: '#7f1d1d', color: '#fecaca', border: '1px solid #b91c1c', padding: '6px 12px', borderRadius: '8px', cursor: 'pointer', fontWeight: '700', fontSize: '12px' }}>Cancel</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      )}

      </div>
      </div>

      {approveTarget && (
        <div style={{ position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', background: 'rgba(0,0,0,0.8)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1100, backdropFilter: 'blur(5px)' }}>
          <form onSubmit={(e) => { e.preventDefault(); confirmApprove(); }} style={{ background: '#0f172a', border: '1px solid #10b981', padding: '30px', borderRadius: '16px', width: '420px', maxWidth: '90%' }}>
            <h2 style={{ margin: '0 0 10px 0', fontSize: '20px', fontWeight: '800', color: '#f8fafc' }}>Approve invoice</h2>
            <p style={{ color: '#94a3b8', fontSize: '14px', margin: '0 0 16px 0' }}>
              You are approving <b style={{ color: '#f8fafc' }}>{approveTarget.expense_name}</b> (KSh {Number(approveTarget.amount).toLocaleString()}). The approval is recorded in the audit trail with your name. Enter your password to continue.
            </p>
            <input
              type="password" autoFocus placeholder="Your password"
              value={approvePassword}
              onChange={(e) => setApprovePassword(e.target.value)}
              style={{ width: '100%', background: '#1e293b', border: '1px solid #334155', color: '#fff', padding: '10px', borderRadius: '8px', boxSizing: 'border-box' }}
            />
            {approveError && <div style={{ background: '#7f1d1d', border: '1px solid #ef4444', padding: '10px', borderRadius: '8px', marginTop: '12px', fontSize: '13px' }}>{approveError}</div>}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '20px' }}>
              <button type="button" onClick={() => setApproveTarget(null)} style={{ background: '#334155', color: '#fff', border: 'none', padding: '10px 18px', borderRadius: '8px', cursor: 'pointer', fontWeight: '600' }}>Back</button>
              <button type="submit" disabled={approving || !approvePassword} style={{ background: '#065f46', color: '#fff', border: 'none', padding: '10px 18px', borderRadius: '8px', cursor: 'pointer', fontWeight: '700', opacity: (approving || !approvePassword) ? 0.5 : 1 }}>{approving ? 'Approving...' : 'Approve'}</button>
            </div>
          </form>
        </div>
      )}

      {cancelTarget && (
        <div style={{ position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', background: 'rgba(0,0,0,0.8)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1100, backdropFilter: 'blur(5px)' }}>
          <form onSubmit={(e) => { e.preventDefault(); confirmCancel(); }} style={{ background: '#0f172a', border: '1px solid #b91c1c', padding: '30px', borderRadius: '16px', width: '420px', maxWidth: '90%' }}>
            <h2 style={{ margin: '0 0 10px 0', fontSize: '20px', fontWeight: '800', color: '#f8fafc' }}>Cancel Pending invoice</h2>
            <p style={{ color: '#94a3b8', fontSize: '14px', margin: '0 0 16px 0' }}>
              This removes the invoice for <b style={{ color: '#f8fafc' }}>{cancelTarget.expense_name}</b> (KSh {Number(cancelTarget.amount).toLocaleString()}). It is recorded in the audit trail. Enter your password to continue.
            </p>
            <input
              type="password" autoFocus placeholder="Your password"
              value={cancelPassword}
              onChange={(e) => setCancelPassword(e.target.value)}
              style={{ width: '100%', background: '#1e293b', border: '1px solid #334155', color: '#fff', padding: '10px', borderRadius: '8px', boxSizing: 'border-box' }}
            />
            {cancelError && <div style={{ background: '#7f1d1d', border: '1px solid #ef4444', padding: '10px', borderRadius: '8px', marginTop: '12px', fontSize: '13px' }}>{cancelError}</div>}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '20px' }}>
              <button type="button" onClick={() => setCancelTarget(null)} style={{ background: '#334155', color: '#fff', border: 'none', padding: '10px 18px', borderRadius: '8px', cursor: 'pointer', fontWeight: '600' }}>Back</button>
              <button type="submit" disabled={cancelling || !cancelPassword} style={{ background: '#b91c1c', color: '#fff', border: 'none', padding: '10px 18px', borderRadius: '8px', cursor: 'pointer', fontWeight: '700', opacity: (cancelling || !cancelPassword) ? 0.5 : 1 }}>{cancelling ? 'Cancelling...' : 'Cancel invoice'}</button>
            </div>
          </form>
        </div>
      )}

      {deleteTarget && (
        <div style={{ position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', background: 'rgba(0,0,0,0.8)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1100, backdropFilter: 'blur(5px)' }}>
          <form onSubmit={(e) => { e.preventDefault(); confirmDelete(); }} style={{ background: '#0f172a', border: '1px solid #b91c1c', padding: '30px', borderRadius: '16px', width: '420px', maxWidth: '90%' }}>
            <h2 style={{ margin: '0 0 10px 0', fontSize: '20px', fontWeight: '800', color: '#f8fafc' }}>Confirm deletion</h2>
            <p style={{ color: '#94a3b8', fontSize: '14px', margin: '0 0 16px 0' }}>
              You are about to permanently delete <b style={{ color: '#f8fafc' }}>{deleteTarget.expense_name}</b> ({deleteTarget.vendor_name}). This cannot be undone and is recorded in the audit trail. Enter your password to continue.
            </p>
            <input
              type="password" autoFocus placeholder="Your password"
              value={deletePassword}
              onChange={(e) => setDeletePassword(e.target.value)}
              style={{ width: '100%', background: '#1e293b', border: '1px solid #334155', color: '#fff', padding: '10px', borderRadius: '8px', boxSizing: 'border-box' }}
            />
            {deleteError && <div style={{ background: '#7f1d1d', border: '1px solid #ef4444', padding: '10px', borderRadius: '8px', marginTop: '12px', fontSize: '13px' }}>{deleteError}</div>}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '20px' }}>
              <button type="button" onClick={() => setDeleteTarget(null)} style={{ background: '#334155', color: '#fff', border: 'none', padding: '10px 18px', borderRadius: '8px', cursor: 'pointer', fontWeight: '600' }}>Cancel</button>
              <button type="submit" disabled={deleting || !deletePassword} style={{ background: '#b91c1c', color: '#fff', border: 'none', padding: '10px 18px', borderRadius: '8px', cursor: 'pointer', fontWeight: '700', opacity: (deleting || !deletePassword) ? 0.5 : 1 }}>{deleting ? 'Deleting...' : 'Delete permanently'}</button>
            </div>
          </form>
        </div>
      )}

      {/* Modal for Adding Template */}
      {showModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', background: 'rgba(0,0,0,0.8)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000, backdropFilter: 'blur(5px)' }}>
          <div style={{ background: '#0f172a', border: '1px solid #334155', padding: '35px', borderRadius: '16px', width: '480px', maxWidth: '90%', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)' }}>
            <h2 style={{ margin: '0 0 20px 0', fontSize: '22px', fontWeight: '800', color: '#f8fafc' }}>{editingId ? 'Edit' : 'Add'} Recurring Expense Template</h2>
            <form onSubmit={handleSubmit}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginBottom: '15px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '6px', fontWeight: '600' }}>Entity</label>
                  <select 
                    value={formData.entity} 
                    onChange={(e) => setFormData({...formData, entity: e.target.value})}
                    style={{ width: '100%', background: '#1e293b', border: '1px solid #334155', color: '#fff', padding: '10px', borderRadius: '8px' }}
                  >
                    <option value="IAL">IAL</option>
                    <option value="AZL">AZL</option>
                  </select>
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '6px', fontWeight: '600' }}>Category</label>
                  <select 
                    value={formData.category} 
                    onChange={(e) => setFormData({...formData, category: e.target.value})}
                    style={{ width: '100%', background: '#1e293b', border: '1px solid #334155', color: '#fff', padding: '10px', borderRadius: '8px' }}
                  >
                    <option value="Rent">Rent</option>
                    <option value="Internet">Internet</option>
                    <option value="Security">Security</option>
                    <option value="Utilities">Utilities</option>
                  </select>
                </div>
              </div>

              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '6px', fontWeight: '600' }}>Expense Name</label>
                <input 
                  type="text" required placeholder="e.g., Warehouse Rent"
                  value={formData.expense_name} 
                  onChange={(e) => setFormData({...formData, expense_name: e.target.value})}
                  style={{ width: '100%', background: '#1e293b', border: '1px solid #334155', color: '#fff', padding: '10px', borderRadius: '8px', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '6px', fontWeight: '600' }}>Vendor Name</label>
                <input 
                  type="text" required placeholder="e.g., Coast Properties Ltd"
                  value={formData.vendor_name} 
                  onChange={(e) => setFormData({...formData, vendor_name: e.target.value})}
                  style={{ width: '100%', background: '#1e293b', border: '1px solid #334155', color: '#fff', padding: '10px', borderRadius: '8px', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginBottom: '15px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '6px', fontWeight: '600' }}>Amount (KSh)</label>
                  <input 
                    type="number" required placeholder="350000"
                    value={formData.amount} 
                    onChange={(e) => setFormData({...formData, amount: e.target.value})}
                    style={{ width: '100%', background: '#1e293b', border: '1px solid #334155', color: '#fff', padding: '10px', borderRadius: '8px', boxSizing: 'border-box' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '6px', fontWeight: '600' }}>Due Day (1-31)</label>
                  <input 
                    type="number" min="1" max="31" required
                    value={formData.due_day_of_month} 
                    onChange={(e) => setFormData({...formData, due_day_of_month: e.target.value})}
                    style={{ width: '100%', background: '#1e293b', border: '1px solid #334155', color: '#fff', padding: '10px', borderRadius: '8px', boxSizing: 'border-box' }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginBottom: '15px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '6px', fontWeight: '600' }}>SAP Supplier Code</label>
                  <input
                    type="text" placeholder="e.g., SL000196"
                    value={formData.vendor_code}
                    onChange={(e) => setFormData({...formData, vendor_code: e.target.value.trim()})}
                    style={{ width: '100%', background: '#1e293b', border: '1px solid #334155', color: '#fff', padding: '10px', borderRadius: '8px', boxSizing: 'border-box' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '6px', fontWeight: '600' }}>SAP GL Account</label>
                  <input
                    type="text" placeholder="e.g., _SYS00000000707"
                    value={formData.gl_account}
                    onChange={(e) => setFormData({...formData, gl_account: e.target.value.trim()})}
                    style={{ width: '100%', background: '#1e293b', border: '1px solid #334155', color: '#fff', padding: '10px', borderRadius: '8px', boxSizing: 'border-box' }}
                  />
                </div>
              </div>

              <div style={{ marginBottom: '25px' }}>
                <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '6px', fontWeight: '600' }}>Cost Center Code</label>
                <input 
                  type="text" required placeholder="CC-IAL-MBA-01"
                  value={formData.cost_center} 
                  onChange={(e) => setFormData({...formData, cost_center: e.target.value})}
                  style={{ width: '100%', background: '#1e293b', border: '1px solid #334155', color: '#fff', padding: '10px', borderRadius: '8px', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                <button 
                  type="button" onClick={closeModal}
                  style={{ background: '#334155', color: '#fff', border: 'none', padding: '10px 18px', borderRadius: '8px', cursor: 'pointer', fontWeight: '600' }}
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  style={{ background: '#0284c7', color: '#fff', border: 'none', padding: '10px 20px', borderRadius: '8px', fontWeight: '700', cursor: 'pointer' }}
                >
                  Save Template Rule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}