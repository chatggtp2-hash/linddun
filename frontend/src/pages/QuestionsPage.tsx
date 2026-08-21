import React, { useEffect, useState } from 'react'
import { api } from '../services/api'
import type { Category, Question, QuestionMapping, QuestionOption, TreeNode } from '../types'

const emptyOption = (): QuestionOption => ({ label: '', value: '', risk_score: 1, risk_level: 'LOW', display_order: 0 })

export default function QuestionsPage() {
  const [questions, setQuestions] = useState<Question[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [nodes, setNodes] = useState<any[]>([])
  const [editing, setEditing] = useState<Question | null>(null)
  const [showForm, setShowForm] = useState(false)

  function load() {
    api.get('/api/questions').then((r) => setQuestions(r.data))
  }

  useEffect(() => {
    load()
    api.get('/api/linddun/categories').then((r) => setCategories(r.data))
    api.get('/api/linddun/nodes').then((r) => setNodes(r.data))
  }, [])

  function startNew() {
    setEditing({
      id: '', text: '', question_type: 'YES_NO', weight: 1, display_order: questions.length,
      is_mandatory: true, is_active: true,
      options: [
        { label: 'Yes', value: 'YES', risk_score: 5, risk_level: 'HIGH', display_order: 0 },
        { label: 'No', value: 'NO', risk_score: 1, risk_level: 'LOW', display_order: 1 },
      ],
      mappings: [{ category_id: categories[0]?.id || '', node_id: null }],
    } as Question)
    setShowForm(true)
  }

  function startEdit(q: Question) {
    setEditing({ ...q })
    setShowForm(true)
  }

  async function handleSave() {
    if (!editing) return
    const payload = {
      text: editing.text,
      help_text: editing.help_text,
      question_type: editing.question_type,
      weight: editing.weight,
      display_order: editing.display_order,
      is_mandatory: editing.is_mandatory,
      is_active: editing.is_active,
      options: editing.options.map((o) => ({ ...o, risk_score: Number(o.risk_score) })),
      mappings: editing.mappings.map((m) => ({ category_id: m.category_id, node_id: m.node_id || null })),
    }
    if (editing.id) {
      await api.put(`/api/questions/${editing.id}`, payload)
    } else {
      await api.post('/api/questions', payload)
    }
    setShowForm(false)
    setEditing(null)
    load()
  }

  async function handleDeactivate(id: string) {
    await api.delete(`/api/questions/${id}`)
    load()
  }

  function updateOption(idx: number, field: keyof QuestionOption, value: any) {
    if (!editing) return
    const options = [...editing.options]
    options[idx] = { ...options[idx], [field]: value }
    setEditing({ ...editing, options })
  }

  function addOption() {
    if (!editing) return
    setEditing({ ...editing, options: [...editing.options, emptyOption()] })
  }

  function updateMapping(field: 'category_id' | 'node_id', value: string) {
    if (!editing) return
    const mappings = [{ category_id: editing.mappings[0]?.category_id || '', node_id: editing.mappings[0]?.node_id || null }]
    ;(mappings[0] as any)[field] = value || null
    setEditing({ ...editing, mappings })
  }

  const selectedCategoryId = editing?.mappings[0]?.category_id
  const filteredNodes = nodes.filter((n) => n.category_id === selectedCategoryId)

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <div>
          <h2 className="page-title">Question Management</h2>
          <p className="page-subtitle">Create and map questions to LINDDUN threats without touching source code</p>
        </div>
        <button className="btn" onClick={startNew}>+ New Question</button>
      </div>

      {showForm && editing && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="form-row">
            <label>Question Text</label>
            <textarea value={editing.text} onChange={(e) => setEditing({ ...editing, text: e.target.value })} rows={2} />
          </div>
          <div className="form-row">
            <label>Help Text</label>
            <input type="text" value={editing.help_text || ''} onChange={(e) => setEditing({ ...editing, help_text: e.target.value })} />
          </div>
          <div className="grid grid-3">
            <div className="form-row">
              <label>Type</label>
              <select value={editing.question_type} onChange={(e) => setEditing({ ...editing, question_type: e.target.value as any })}>
                <option value="YES_NO">Yes / No</option>
                <option value="SINGLE_CHOICE">Single Choice</option>
                <option value="MULTIPLE_CHOICE">Multiple Choice</option>
                <option value="TEXT">Optional Text Response</option>
              </select>
            </div>
            <div className="form-row">
              <label>Weight</label>
              <input type="number" step="0.1" value={editing.weight} onChange={(e) => setEditing({ ...editing, weight: Number(e.target.value) })} />
            </div>
            <div className="form-row">
              <label>Mandatory?</label>
              <select value={editing.is_mandatory ? 'yes' : 'no'} onChange={(e) => setEditing({ ...editing, is_mandatory: e.target.value === 'yes' })}>
                <option value="yes">Yes</option>
                <option value="no">No</option>
              </select>
            </div>
          </div>

          <h4>Answer Options & Risk Scoring</h4>
          {editing.options.map((opt, idx) => (
            <div key={idx} className="grid grid-4" style={{ marginBottom: 8, alignItems: 'end' }}>
              <div><label>Label</label><input type="text" value={opt.label} onChange={(e) => updateOption(idx, 'label', e.target.value)} /></div>
              <div><label>Value</label><input type="text" value={opt.value} onChange={(e) => updateOption(idx, 'value', e.target.value)} /></div>
              <div><label>Risk Score</label><input type="number" value={opt.risk_score} onChange={(e) => updateOption(idx, 'risk_score', e.target.value)} /></div>
              <div>
                <label>Risk Level</label>
                <select value={opt.risk_level} onChange={(e) => updateOption(idx, 'risk_level', e.target.value)}>
                  <option>LOW</option><option>MEDIUM</option><option>HIGH</option><option>CRITICAL</option>
                </select>
              </div>
            </div>
          ))}
          <button className="btn secondary" type="button" onClick={addOption} style={{ marginBottom: 20 }}>+ Add Option</button>

          <h4>LINDDUN Mapping</h4>
          <div className="grid grid-2">
            <div className="form-row">
              <label>Category</label>
              <select value={selectedCategoryId || ''} onChange={(e) => updateMapping('category_id', e.target.value)}>
                <option value="">Select category</option>
                {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div className="form-row">
              <label>Threat Node</label>
              <select value={editing.mappings[0]?.node_id || ''} onChange={(e) => updateMapping('node_id', e.target.value)}>
                <option value="">(category-level only)</option>
                {filteredNodes.map((n) => <option key={n.id} value={n.id}>{n.name}</option>)}
              </select>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 10, marginTop: 16 }}>
            <button className="btn" onClick={handleSave}>Save Question</button>
            <button className="btn secondary" onClick={() => { setShowForm(false); setEditing(null) }}>Cancel</button>
          </div>
        </div>
      )}

      <div className="card">
        <table>
          <thead><tr><th>Question</th><th>Type</th><th>Weight</th><th>Mandatory</th><th>Active</th><th></th></tr></thead>
          <tbody>
            {questions.map((q) => (
              <tr key={q.id}>
                <td>{q.text}</td>
                <td>{q.question_type}</td>
                <td>{q.weight}</td>
                <td>{q.is_mandatory ? 'Yes' : 'No'}</td>
                <td>{q.is_active ? 'Yes' : 'No'}</td>
                <td style={{ display: 'flex', gap: 6 }}>
                  <button className="btn secondary" style={{ padding: '4px 10px', fontSize: 12 }} onClick={() => startEdit(q)}>Edit</button>
                  {q.is_active && (
                    <button className="btn danger" style={{ padding: '4px 10px', fontSize: 12 }} onClick={() => handleDeactivate(q.id)}>Deactivate</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
