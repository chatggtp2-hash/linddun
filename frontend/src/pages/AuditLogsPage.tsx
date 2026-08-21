import React, { useEffect, useState } from 'react'
import { api } from '../services/api'

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<any[]>([])

  useEffect(() => {
    api.get('/api/audit-logs').then((r) => setLogs(r.data))
  }, [])

  return (
    <div>
      <h2 className="page-title">Audit Logs</h2>
      <p className="page-subtitle">Every login, question change, submission, and risk calculation is recorded here</p>
      <div className="card">
        <table>
          <thead><tr><th>Timestamp</th><th>Action</th><th>Entity</th><th>Entity ID</th><th>IP</th></tr></thead>
          <tbody>
            {logs.map((l) => (
              <tr key={l.id}>
                <td>{new Date(l.timestamp).toLocaleString()}</td>
                <td>{l.action}</td>
                <td>{l.entity}</td>
                <td style={{ fontSize: 11 }}>{l.entity_id}</td>
                <td>{l.ip_address || '—'}</td>
              </tr>
            ))}
            {logs.length === 0 && <tr><td colSpan={5} className="empty-state">No audit entries yet</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}
