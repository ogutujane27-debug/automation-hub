import React, { useState } from 'react';
import axios from 'axios';

const API = 'http://127.0.0.1:8000/api';

export default function Login({ onLoggedIn }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      const r = await axios.post(`${API}/login/`, { username, password });
      onLoggedIn(r.data);
    } catch (err) {
      if (err.response && err.response.status === 429) setError('Too many attempts. Wait a minute and try again.');
      else if (err.response && err.response.data && err.response.data.error) setError(err.response.data.error);
      else setError('Cannot reach the server.');
    } finally {
      setBusy(false);
    }
  };

  const input = { width: '100%', padding: '12px', marginTop: '6px', marginBottom: '16px', borderRadius: '8px', border: '1px solid #334155', background: '#0f172a', color: '#f8fafc', boxSizing: 'border-box' };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#020617' }}>
      <form onSubmit={submit} autoComplete="off" style={{ width: '340px', padding: '32px', borderRadius: '16px', background: '#1e293b', color: '#cbd5e1' }}>
        <h2 style={{ marginTop: 0, color: '#f8fafc' }}>AUTO-12: Recurring Invoices</h2>
        <label>Username<input style={input} name="auto12-user" autoComplete="off" value={username} onChange={e => setUsername(e.target.value)} autoFocus /></label>
        <label>Password<input style={input} name="auto12-pass" type="password" autoComplete="new-password" value={password} onChange={e => setPassword(e.target.value)} /></label>
        {error && <div style={{ color: '#fca5a5', marginBottom: '12px' }}>{error}</div>}
        <button type="submit" disabled={busy} style={{ width: '100%', padding: '12px', borderRadius: '8px', border: 'none', background: '#0284c7', color: '#fff', fontWeight: '700', cursor: 'pointer' }}>
          {busy ? 'Signing in...' : 'Sign in'}
        </button>
      </form>
    </div>
  );
}
