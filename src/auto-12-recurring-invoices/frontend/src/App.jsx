import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import Auto12Dashboard from './Auto12Dashboard';
import Login from './Login';

const API = 'http://127.0.0.1:8000/api';
const IDLE_MINUTES = 30;

function readStored() {
  try { return JSON.parse(sessionStorage.getItem('auto12_auth')); } catch (e) { return null; }
}
function applyToken(token) {
  if (token) axios.defaults.headers.common.Authorization = `Token ${token}`;
  else delete axios.defaults.headers.common.Authorization;
}

const stored = readStored();
if (stored && stored.token) applyToken(stored.token);

axios.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response && err.response.status === 401) window.dispatchEvent(new Event('auto12-unauthorized'));
    return Promise.reject(err);
  }
);

function App() {
  const [auth, setAuth] = useState(stored);
  const dirtyRef = useRef(false);

  const clearSession = () => {
    applyToken(null);
    try { sessionStorage.removeItem('auto12_auth'); } catch (e) {}
    dirtyRef.current = false;
    setAuth(null);
  };

  const logout = async (force) => {
    if (!force && dirtyRef.current) {
      const discard = window.confirm('You have an open form with unsaved changes.\n\nOK = discard them and log out\nCancel = stay and save first');
      if (!discard) return;
    }
    try { await axios.post(`${API}/logout/`); } catch (e) {}
    clearSession();
  };

  const handleLoggedIn = (data) => {
    applyToken(data.token);
    try { sessionStorage.setItem('auto12_auth', JSON.stringify(data)); } catch (e) {}
    setAuth(data);
  };

  useEffect(() => {
    if (!auth) return undefined;
    const onUnauthorized = () => clearSession();
    window.addEventListener('auto12-unauthorized', onUnauthorized);
    let timer;
    const reset = () => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        alert('You were logged out after ' + IDLE_MINUTES + ' minutes of inactivity.');
        logout(true);
      }, IDLE_MINUTES * 60 * 1000);
    };
    const events = ['mousemove', 'keydown', 'click', 'scroll'];
    events.forEach(ev => window.addEventListener(ev, reset));
    reset();
    const beforeUnload = (e) => {
      if (dirtyRef.current) { e.preventDefault(); e.returnValue = ''; }
    };
    window.addEventListener('beforeunload', beforeUnload);
    return () => {
      clearTimeout(timer);
      events.forEach(ev => window.removeEventListener(ev, reset));
      window.removeEventListener('beforeunload', beforeUnload);
      window.removeEventListener('auto12-unauthorized', onUnauthorized);
    };
  }, [auth]);

  if (!auth) return <Login onLoggedIn={handleLoggedIn} />;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '14px', padding: '10px 30px', background: '#020617', color: '#94a3b8', fontSize: '13px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ background: 'linear-gradient(135deg, #0ea5e9, #2563eb)', width: '34px', height: '34px', borderRadius: '9px', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 4px 12px rgba(14,165,233,0.3)', fontSize: '17px', color: '#fff' }}>{'\u26A1'}</div>
          <div>
            <div style={{ fontSize: '17px', fontWeight: '800', color: '#f8fafc', letterSpacing: '-0.3px', lineHeight: 1.2 }}>AUTO-12: Recurring Invoices</div>
            <div style={{ fontSize: '12px', color: '#94a3b8' }}>Recurring monthly invoice rules for <span style={{ color: '#38bdf8', fontWeight: '600' }}>IAL</span> & <span style={{ color: '#38bdf8', fontWeight: '600' }}>AZL</span> Operating Entities</div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <span>{auth.username} ({auth.role})</span>
        <button onClick={() => logout(false)} style={{ background: '#7f1d1d', color: '#fecaca', border: '1px solid #b91c1c', padding: '6px 14px', borderRadius: '8px', cursor: 'pointer', fontWeight: '700' }}>Log out</button>
        </div>
      </div>
      <Auto12Dashboard role={auth.role} onDirtyChange={(d) => { dirtyRef.current = d; }} />
    </div>
  );
}

export default App;
