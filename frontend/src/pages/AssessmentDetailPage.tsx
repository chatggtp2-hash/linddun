import React, { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../services/api'
import type { Assessment, AssessmentQuestionItem, Evidence } from '../types'

export default function AssessmentDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [assessment, setAssessment] = useState<Assessment | null>(null)
  const [questions, setQuestions] = useState<AssessmentQuestionItem[]>([])
  const [index, setIndex] = useState(0)
  const [selected, setSelected] = useState<string | undefined>(undefined)
  const [evidenceList, setEvidenceList] = useState<Evidence[]>([])
  const [saving, setSaving] = useState(false)
  const [submitError, setSubmitError] = useState<string[]>([])

  function load() {
    api.get(`/api/assessments/${id}`).then((r) => setAssessment(r.data))
    api.get(`/api/assessments/${id}/questions`).then((r) => setQuestions(r.data))
    api.get(`/api/evidence/assessment/${id}`).then((r) => setEvidenceList(r.data))
  }

  useEffect(load, [id])

  const current = questions[index]

  useEffect(() => {
    setSelected(current?.existing_answer?.selected_option_id)
  }, [index, questions])

  async function saveAnswer(optionId?: string) {
    if (!current) return
    setSaving(true)
    try {
      await api.post(`/api/assessments/${id}/answers`, {
        question_id: current.question_id,
        selected_option_id: optionId,
      })
    } finally {
      setSaving(false)
    }
  }

  async function handleSelect(optionId: string) {
    setSelected(optionId)
    await saveAnswer(optionId)
  }

  async function handleNext() {
    if (index < questions.length - 1) setIndex(index + 1)
  }
  function handlePrev() {
    if (index > 0) setIndex(index - 1)
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file || !current) return
    const form = new FormData()
    form.append('assessment_id', id!)
    form.append('question_id', current.question_id)
    form.append('file', file)
    await api.post('/api/evidence/upload', form, { headers: { 'Content-Type': 'multipart/form-data' } })
    api.get(`/api/evidence/assessment/${id}`).then((r) => setEvidenceList(r.data))
  }

  async function handleSubmit() {
    setSubmitError([])
    try {
      await api.post(`/api/assessments/${id}/submit`)
      navigate(`/assessments/${id}/result`)
    } catch (err: any) {
      const missing = err.response?.data?.missing
      setSubmitError(missing || [err.response?.data?.message || 'Submit failed'])
    }
  }

  if (!assessment || questions.length === 0) {
    return <div className="empty-state">Loading assessment…</div>
  }

  const answeredCount = questions.filter((q) => q.existing_answer).length
  const progressPct = Math.round((answeredCount / questions.length) * 100)
  const questionEvidence = evidenceList.filter((e) => e.question_id === current?.question_id)

  return (
    <div>
      <h2 className="page-title">{assessment.name}</h2>
      <p className="page-subtitle">Progress: {answeredCount} / {questions.length} answered</p>
      <div className="progress-bar-track" style={{ marginBottom: 20 }}>
        <div className="progress-bar-fill" style={{ width: `${progressPct}%` }} />
      </div>

      <div className="question-panel">
        <div className="card">
          <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 8 }}>Question {index + 1} of {questions.length}</div>
          <h3 style={{ marginTop: 0 }}>{current.text}</h3>
          {current.help_text && <p style={{ color: '#6b7280', fontSize: 13 }}>{current.help_text}</p>}

          <div style={{ marginTop: 16 }}>
            {current.options.map((opt) => (
              <div
                key={opt.id}
                className={`option-row ${selected === opt.id ? 'selected' : ''}`}
                onClick={() => handleSelect(opt.id)}
              >
                <input type="radio" checked={selected === opt.id} onChange={() => handleSelect(opt.id)} />
                {opt.label}
              </div>
            ))}
          </div>

          <div style={{ marginTop: 20 }}>
            <label>Evidence</label>
            <input type="file" onChange={handleUpload} />
            {questionEvidence.length > 0 && (
              <ul style={{ fontSize: 13, marginTop: 8 }}>
                {questionEvidence.map((ev) => <li key={ev.id}>{ev.file_name}</li>)}
              </ul>
            )}
          </div>

          <div style={{ display: 'flex', gap: 10, marginTop: 24 }}>
            <button className="btn secondary" onClick={handlePrev} disabled={index === 0}>Previous</button>
            {index < questions.length - 1 ? (
              <button className="btn" onClick={handleNext}>Next</button>
            ) : (
              <button className="btn" onClick={handleSubmit}>Submit Assessment</button>
            )}
          </div>
          {submitError.length > 0 && (
            <div className="error-text" style={{ marginTop: 12 }}>
              Please answer: {submitError.join(', ')}
            </div>
          )}
        </div>

        <div className="card">
          <h4 style={{ marginTop: 0, fontSize: 13, color: '#6b7280', textTransform: 'uppercase' }}>LINDDUN Mapping</h4>
          <div style={{ fontSize: 12, color: '#6b7280' }}>Category</div>
          <div style={{ fontWeight: 700, marginBottom: 10 }}>{current.mapped_category || '—'}</div>
          <div style={{ fontSize: 12, color: '#6b7280' }}>This answer will automatically update the LINDDUN risk tree once submitted.</div>
        </div>
      </div>
    </div>
  )
}
