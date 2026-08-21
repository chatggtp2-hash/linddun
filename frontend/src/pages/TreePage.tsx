import React, { useEffect, useState } from 'react'
import { api } from '../services/api'
import LinddunTreeView from '../components/LinddunTreeView'
import type { Assessment, TreeNode } from '../types'

export default function TreePage() {
  const [tree, setTree] = useState<TreeNode[]>([])
  const [assessments, setAssessments] = useState<Assessment[]>([])
  const [assessmentId, setAssessmentId] = useState<string>('')

  useEffect(() => {
    api.get('/api/assessments').then((r) => setAssessments(r.data.filter((a: Assessment) => a.overall_score !== null)))
  }, [])

  useEffect(() => {
    const url = assessmentId ? `/api/linddun/tree?assessment_id=${assessmentId}` : '/api/linddun/tree'
    api.get(url).then((r) => setTree(r.data))
  }, [assessmentId])

  return (
    <div>
      <h2 className="page-title">LINDDUN Tree</h2>
      <p className="page-subtitle">Automatically generated from the framework structure and, when selected, live assessment risk scores</p>

      <div className="card" style={{ marginBottom: 16 }}>
        <label>View risk from assessment</label>
        <select value={assessmentId} onChange={(e) => setAssessmentId(e.target.value)}>
          <option value="">Framework structure only (no scores)</option>
          {assessments.map((a) => (
            <option key={a.id} value={a.id}>{a.name}</option>
          ))}
        </select>
      </div>

      <div className="card">
        <LinddunTreeView tree={tree} />
      </div>
    </div>
  )
}
