import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

export default function RecurringInvoicesManager() {
  const [activeTab, setActiveTab] = useState('templates');
  const [templates, setTemplates] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // New template form state
  const [formData, setFormData] = useState({
    entity: 'IAL',
    expense_name: '',
    vendor_name: '',
    amount: '',
    cost_center: '',
    due_day_of_month: 28,
    is_active: true,
  });

  // Fetch templates and logs on mount
  useEffect(() => {
    fetchData();
  }, [activeTab]);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      if (activeTab === 'templates' || activeTab === 'create') {
        const res = await axios.get(`${API_BASE_URL}/recurring-templates/`);
        setTemplates(res.data);
      } else if (activeTab === 'logs') {
        const res = await axios.get(`${API_BASE_URL}/invoice-logs/`);
        setLogs(res.data);
      }
    } catch (err) {
      setError('Failed to connect to Django backend API. Ensure the server is running.');
    }
    setLoading(false);
  };

  const handleTrigger = async (id) => {
    try {
      const res = await axios.post(`${API_BASE_URL}/recurring-templates/${id}/trigger/`);
      alert(`Successfully generated invoice: ${res.data.invoice_number}`);
      fetchData();
    } catch (err) {
      alert(`Failed to trigger invoice: ${err.response?.data?.error || err.message}`);
    }
  };

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_BASE_URL}/recurring-templates/`, formData);
      alert('Recurring template created successfully!');
      setFormData({
        entity: 'IAL',
        expense_name: '',
        vendor_name: '',
        amount: '',
        cost_center: '',
        due_day_of_month: 28,
        is_active: true,
      });
      setActiveTab('templates');
    } catch (err) {
      alert('Error creating template. Check inputs.');
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6 font-sans">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800">📄 AUTO-12: Recurring Invoices (IAL & AZL)</h1>
        <p className="text-gray-600">Manage recurring overhead expenses (Rent, Internet, Security, etc.)</p>
      </header>

      {/* Navigation Tabs */}
      <div className="flex border-b border-gray-200 mb-6">
        <button
          className={`py-2 px-4 font-semibold ${activeTab === 'templates' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500'}`}
          onClick={() => setActiveTab('templates')}
        >
          Active Templates
        </button>
        <button
          className={`py-2 px-4 font-semibold ${activeTab === 'create' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500'}`}
          onClick={() => setActiveTab('create')}
        >
          Add New Rule
        </button>
        <button
          className={`py-2 px-4 font-semibold ${activeTab === 'logs' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500'}`}
          onClick={() => setActiveTab('logs')}
        >
          Generated Audit Logs
        </button>
      </div>

      {error && <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">{error}</div>}
      {loading && <p className="text-gray-500">Loading data from Django API...</p>}

      {/* 1. ACTIVE TEMPLATES TAB */}
      {activeTab === 'templates' && !loading && (
        <div className="grid gap-4">
          {templates.length === 0 ? (
            <p className="text-gray-500">No recurring invoice templates found.</p>
          ) : (
            templates.map((t) => (
              <div key={t.id} className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm flex justify-between items-center">
                <div>
                  <span className={`inline-block px-2 py-1 text-xs font-bold rounded mr-2 ${t.entity === 'IAL' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'}`}>
                    {t.entity}
                  </span>
                  <h3 className="text-lg font-semibold inline">{t.expense_name}</h3>
                  <p className="text-sm text-gray-600 mt-1">Vendor: {t.vendor_name} | Cost Center: {t.cost_center}</p>
                  <p className="text-sm text-gray-500">Due Day: {t.due_day_of_month}th of every month | Last Generated: {t.last_generated || 'Never'}</p>
                </div>
                <div className="text-right">
                  <p className="text-xl font-bold text-gray-900 mb-2">KSh {Number(t.amount).toLocaleString()}</p>
                  <button
                    onClick={() => handleTrigger(t.id)}
                    className="bg-green-600 hover:bg-green-700 text-white text-sm font-semibold py-2 px-4 rounded shadow"
                  >
                    ⚡ Force Trigger
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* 2. CREATE NEW TEMPLATE TAB */}
      {activeTab === 'create' && (
        <form onSubmit={handleCreateSubmit} className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm max-w-2xl">
          <h2 className="text-xl font-semibold mb-4">Create Recurring Expense Rule</h2>
          
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Entity</label>
              <select
                className="w-full border border-gray-300 rounded p-2"
                value={formData.entity}
                onChange={(e) => setFormData({ ...formData, entity: e.target.value })}
              >
                <option value="IAL">IAL</option>
                <option value="AZL">AZL</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Expense Name</label>
              <input
                type="text"
                required
                className="w-full border border-gray-300 rounded p-2"
                placeholder="e.g., Office Rent - Mombasa"
                value={formData.expense_name}
                onChange={(e) => setFormData({ ...formData, expense_name: e.target.value })}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Vendor Name</label>
              <input
                type="text"
                required
                className="w-full border border-gray-300 rounded p-2"
                placeholder="e.g., Coastal Properties"
                value={formData.vendor_name}
                onChange={(e) => setFormData({ ...formData, vendor_name: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Monthly Amount (KSh)</label>
              <input
                type="number"
                step="0.01"
                required
                className="w-full border border-gray-300 rounded p-2"
                value={formData.amount}
                onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Cost Center Code</label>
              <input
                type="text"
                required
                className="w-full border border-gray-300 rounded p-2"
                placeholder="e.g., CC-OPS-01"
                value={formData.cost_center}
                onChange={(e) => setFormData({ ...formData, cost_center: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Due Day of Month (1-31)</label>
              <input
                type="number"
                min="1"
                max="31"
                required
                className="w-full border border-gray-300 rounded p-2"
                value={formData.due_day_of_month}
                onChange={(e) => setFormData({ ...formData, due_day_of_month: Number(e.target.value) })}
              />
            </div>
          </div>

          <button
            type="submit"
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-6 rounded shadow mt-4"
          >
            Save Recurring Rule
          </button>
        </form>
      )}

      {/* 3. GENERATED AUDIT LOGS TAB */}
      {activeTab === 'logs' && !loading && (
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-100 border-b border-gray-200 text-sm text-gray-700">
                <th className="p-3">Invoice Number</th>
                <th className="p-3">Entity</th>
                <th className="p-3">Expense</th>
                <th className="p-3">Vendor</th>
                <th className="p-3">Amount</th>
                <th className="p-3">Generated Date</th>
                <th className="p-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {logs.length === 0 ? (
                <tr>
                  <td colSpan="7" className="p-4 text-center text-gray-500">No invoice logs recorded yet.</td>
                </tr>
              ) : (
                logs.map((l) => (
                  <tr key={l.id} className="border-b border-gray-100 text-sm">
                    <td className="p-3 font-mono font-medium">{l.invoice_number}</td>
                    <td className="p-3">{l.entity}</td>
                    <td className="p-3">{l.expense_name}</td>
                    <td className="p-3">{l.vendor_name}</td>
                    <td className="p-3 font-semibold">KSh {Number(l.amount).toLocaleString()}</td>
                    <td className="p-3">{l.generated_date}</td>
                    <td className="p-3">
                      <span className="px-2 py-1 text-xs font-semibold rounded bg-yellow-100 text-yellow-800">
                        {l.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}