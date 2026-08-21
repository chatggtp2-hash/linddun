import React, { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { api } from '../services/api'
import RiskBadge from '../components/RiskBadge'

const COLORS: Record<string, string> = { LOW: '#16a34a', MEDIUM: '#ca8a04', HIGH: '#ea580c', CRITICAL: '#dc2626' }

export default function DashboardPage() {
  const [summary, setSummary] = useState<any>(null)
  const [distribution, setDistribution] = useState<any>(null)
  const [linddunRisk, setLinddunRisk] = useState<any[]>([])

  useEffect(() => {
    api.get('/api/dashboard/summary').then((r) => setSummary(r.data))
    api.get('/api/dashboard/risk-distribution').then((r) => setDistribution(r.data))
    api.get('/api/dashboard/linddun-risk').then((r) => setLinddunRisk(r.data))
  }, [])

  const pieData = distribution
    ? Object.entries(distribution).map(([k, v]) => ({ name: k, value: v as number }))
    : []

  const topThreats = [...linddunRisk].sort((a, b) => b.score - a.score).slice(0, 5)

  return (
    <div>
      <h2 className="page-title">Dashboard</h2>
      <p className="page-subtitle">Executive overview of privacy risk across all assessments</p>

      <div className="grid grid-4" style={{ marginBottom: 20 }}>
        <div className="card stat-card">
          <div className="stat-label">Total Assessments</div>
          <div className="stat-value">{summary?.total_assessments ?? '—'}</div>
        </div>
        <div className="card stat-card">
          <div className="stat-label">Completed</div>
          <div className="stat-value">{summary?.completed_assessments ?? '—'}</div>
        </div>
        <div className="card stat-card">
          <div className="stat-label">In Progress</div>
          <div className="stat-value">{summary?.in_progress_assessments ?? '—'}</div>
        </div>
        <div className="card stat-card">
          <div className="stat-label">Overall Avg Risk Score</div>
          <div className="stat-value">{summary?.overall_risk_score ?? '—'}</div>
        </div>
      </div>

      <div className="grid grid-4" style={{ marginBottom: 20 }}>
        <div className="card stat-card">
          <div className="stat-label">High Risk Assessments</div>
          <div className="stat-value" style={{ color: '#ea580c' }}>{summary?.high_risk_assessments ?? '—'}</div>
        </div>
        <div className="card stat-card">
          <div className="stat-label">Critical Risk Assessments</div>
          <div className="stat-value" style={{ color: '#dc2626' }}>{summary?.critical_risk_assessments ?? '—'}</div>
        </div>
      </div>

      <div className="grid grid-2" style={{ marginBottom: 20 }}>
        <div className="card">
          <h3 style={{ marginTop: 0, fontSize: 15 }}>LINDDUN Category Risk</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={linddunRisk} layout="vertical" margin={{ left: 20 }}>
              <XAxis type="number" domain={[0, 'dataMax + 10']} />
              <YAxis type="category" dataKey="category" width={120} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="score" radius={[0, 4, 4, 0]}>
                {linddunRisk.map((entry, idx) => (
                  <Cell key={idx} fill={COLORS[entry.risk_level] || '#94a3b8'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h3 style={{ marginTop: 0, fontSize: 15 }}>Risk Distribution (Assessments)</h3>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label>
                {pieData.map((entry, idx) => (
                  <Cell key={idx} fill={COLORS[entry.name] || '#94a3b8'} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0, fontSize: 15 }}>Top 5 Highest-Risk Categories</h3>
        <table>
          <thead>
            <tr><th>#</th><th>Category</th><th>Score</th><th>Risk</th></tr>
          </thead>
          <tbody>
            {topThreats.map((t, i) => (
              <tr key={t.code}>
                <td>{i + 1}</td>
                <td>{t.category}</td>
                <td>{t.score}</td>
                <td><RiskBadge level={t.risk_level} /></td>
              </tr>
            ))}
            {topThreats.length === 0 && (
              <tr><td colSpan={4} className="empty-state">No completed assessments yet</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
