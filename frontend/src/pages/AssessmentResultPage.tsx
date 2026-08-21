import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../services/api'
import RiskBadge from '../components/RiskBadge'
import LinddunTreeView from '../components/LinddunTreeView'
import type { AssessmentResult, Evidence, TreeNode } from '../types'

export default function AssessmentResultPage() {
  const { id } = useParams()
  const [result, setResult] = useState<AssessmentResult | null>(null)
  const [tree, setTree] = useState<TreeNode[]>([])
  const [evidence, setEvidence] = useState<Evidence[]>([])
  const [tab, setTab] = useState<'summary' | 'tree' | 'evidence'>('summary')

  useEffect(() => {
    api.get(`/api/assessments/${id}/result`).then((r) => setResult(r.data))
    api.get(`/api/assessments/${id}/tree`).then((r) => setTree(r.data))
    api.get(`/api/evidence/assessment/${id}`).then((r) => setEvidence(r.data))
  }, [id])

  if (!result) return <div className="empty-state">Loading result…</div>

  const { assessment, category_results, top_threats, recommendations } = result

  return (
    <div>
      <h2 className="page-title">{assessment.name} — Result</h2>
      <p className="page-subtitle">
        Submitted {assessment.submitted_at ? new Date(assessment.submitted_at).toLocaleString() : '—'}
      </p>

      <div className="grid grid-2" style={{ marginBottom: 20 }}>
        <div className="card stat-card">
          <div className="stat-label">Overall Risk Score</div>
          <div className="stat-value">{assessment.overall_score}</div>
        </div>
        <div className="card stat-card">
          <div className="stat-label">Overall Risk Level</div>
          <div className="stat-value"><RiskBadge level={assessment.overall_risk_level} /></div>
        </div>
      </div>

      <div className="tab-bar">
        <button className={tab === 'summary' ? 'active' : ''} onClick={() => setTab('summary')}>Summary</button>
        <button className={tab === 'tree' ? 'active' : ''} onClick={() => setTab('tree')}>LINDDUN Tree</button>
        <button className={tab === 'evidence' ? 'active' : ''} onClick={() => setTab('evidence')}>Evidence</button>
      </div>

      {tab === 'summary' && (
        <>
          <div className="card" style={{ marginBottom: 20 }}>
            <h3 style={{ marginTop: 0, fontSize: 15 }}>LINDDUN Risk Summary</h3>
            <table>
              <thead><tr><th>Category</th><th>Score</th><th>Risk</th></tr></thead>
              <tbody>
                {category_results.map((c) => (
                  <tr key={c.category_id}>
                    <td>{c.category_name}</td>
                    <td>{c.score}</td>
                    <td><RiskBadge level={c.risk_level} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="card" style={{ marginBottom: 20 }}>
            <h3 style={{ marginTop: 0, fontSize: 15 }}>Top Threats</h3>
            <table>
              <thead><tr><th>#</th><th>Threat Category</th><th>Risk</th></tr></thead>
              <tbody>
                {top_threats.map((t, i) => (
                  <tr key={i}><td>{i + 1}</td><td>{t.name}</td><td><RiskBadge level={t.risk_level} /></td></tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="card">
            <h3 style={{ marginTop: 0, fontSize: 15 }}>Recommended Actions</h3>
            {recommendations.length === 0 && <p style={{ color: '#6b7280' }}>No specific recommendations triggered — risk levels are within acceptable thresholds.</p>}
            <ul>
              {recommendations.map((r, i) => <li key={i} style={{ marginBottom: 6 }}>{r}</li>)}
            </ul>
          </div>
        </>
      )}

      {tab === 'tree' && (
        <div className="card">
          <LinddunTreeView tree={tree} />
        </div>
      )}

      {tab === 'evidence' && (
        <div className="card">
          <table>
            <thead><tr><th>File</th><th>Type</th><th>Size</th><th>Uploaded</th></tr></thead>
            <tbody>
              {evidence.map((e) => (
                <tr key={e.id}>
                  <td>{e.file_name}</td>
                  <td>{e.file_type}</td>
                  <td>{Math.round(e.file_size / 1024)} KB</td>
                  <td>{new Date(e.uploaded_at).toLocaleString()}</td>
                </tr>
              ))}
              {evidence.length === 0 && <tr><td colSpan={4} className="empty-state">No evidence uploaded</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
