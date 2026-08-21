import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../services/api'
import RiskBadge from '../components/RiskBadge'
import type { Assessment } from '../types'

export default function AssessmentsPage() {
  const [assessments, setAssessments] = useState<Assessment[]>([])
  const [showForm, setShowForm] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [creating, setCreating] = useState(false)
  const navigate = useNavigate()

  function load() {
    api.get('/api/assessments').then((r) => setAssessments(r.data))
  }

  useEffect(load, [])

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    setCreating(true)
    try {
      const res = await api.post('/api/assessments', { name, description, question_ids: [] })
      navigate(`/assessments/${res.data.id}`)
    } finally {
      setCreating(false)
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2 className="page-title">Assessments</h2>
          <p className="page-subtitle">Privacy risk assessments and their status</p>
        </div>
        <button className="btn" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancel' : '+ New Assessment'}
        </button>
      </div>

      {showForm && (
        <form className="card" onSubmit={handleCreate} style={{ marginBottom: 20 }}>
          <div className="form-row">
            <label>Assessment Name</label>
            <input type="text" value={name} onChange={(e) => setName(e.target.value)} required placeholder="e.g. Customer Data Processing Assessment" />
          </div>
          <div className="form-row">
            <label>Description</label>
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={2} />
          </div>
          <button className="btn" type="submit" disabled={creating}>{creating ? 'Creating...' : 'Create Assessment'}</button>
        </form>
      )}

      <div className="card">
        <table>
          <thead>
            <tr><th>Name</th><th>Status</th><th>Risk Score</th><th>Risk Level</th><th>Created</th><th></th></tr>
          </thead>
          <tbody>
            {assessments.map((a) => (
              <tr key={a.id} style={{ cursor: 'pointer' }} onClick={() => navigate(a.status === 'COMPLETED' ? `/assessments/${a.id}/result` : `/assessments/${a.id}`)}>
                <td>{a.name}</td>
                <td>{a.status}</td>
                <td>{a.overall_score ?? '—'}</td>
                <td>{a.overall_risk_level ? <RiskBadge level={a.overall_risk_level} /> : '—'}</td>
                <td>{new Date(a.created_at).toLocaleDateString()}</td>
                <td><a className="btn secondary" style={{ padding: '4px 10px', fontSize: 12 }}>Open</a></td>
              </tr>
            ))}
            {assessments.length === 0 && (
              <tr><td colSpan={6} className="empty-state">No assessments yet — create one to get started</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
