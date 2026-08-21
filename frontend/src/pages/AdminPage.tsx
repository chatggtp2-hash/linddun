import React, { useEffect, useState } from 'react'
import { api } from '../services/api'
import type { Category, User } from '../types'

export default function AdminPage() {
  const [tab, setTab] = useState<'nodes' | 'users'>('nodes')
  const [categories, setCategories] = useState<Category[]>([])
  const [nodes, setNodes] = useState<any[]>([])
  const [users, setUsers] = useState<User[]>([])

  const [newNode, setNewNode] = useState({ category_id: '', parent_id: '', code: '', name: '', description: '' })
  const [newUser, setNewUser] = useState({ email: '', full_name: '', password: '', role: 'ASSESSOR' })

  function loadNodes() {
    api.get('/api/linddun/categories').then((r) => setCategories(r.data))
    api.get('/api/linddun/nodes').then((r) => setNodes(r.data))
  }
  function loadUsers() {
    api.get('/api/users').then((r) => setUsers(r.data))
  }

  useEffect(() => { loadNodes(); loadUsers() }, [])

  async function handleCreateNode(e: React.FormEvent) {
    e.preventDefault()
    await api.post('/api/linddun/nodes', {
      category_id: newNode.category_id,
      parent_id: newNode.parent_id || null,
      code: newNode.code,
      name: newNode.name,
      description: newNode.description,
      display_order: 0,
    })
    setNewNode({ category_id: '', parent_id: '', code: '', name: '', description: '' })
    loadNodes()
  }

  async function toggleNodeActive(node: any) {
    await api.put(`/api/linddun/nodes/${node.id}`, { is_active: !node.is_active })
    loadNodes()
  }

  async function handleCreateUser(e: React.FormEvent) {
    e.preventDefault()
    await api.post('/api/users', newUser)
    setNewUser({ email: '', full_name: '', password: '', role: 'ASSESSOR' })
    loadUsers()
  }

  const nodesInCategory = nodes.filter((n) => n.category_id === newNode.category_id)

  return (
    <div>
      <h2 className="page-title">Admin</h2>
      <p className="page-subtitle">Manage the LINDDUN framework tree and platform users</p>

      <div className="tab-bar">
        <button className={tab === 'nodes' ? 'active' : ''} onClick={() => setTab('nodes')}>LINDDUN Tree Management</button>
        <button className={tab === 'users' ? 'active' : ''} onClick={() => setTab('users')}>User Management</button>
      </div>

      {tab === 'nodes' && (
        <>
          <form className="card" onSubmit={handleCreateNode} style={{ marginBottom: 20 }}>
            <h3 style={{ marginTop: 0, fontSize: 15 }}>Add Threat Node</h3>
            <div className="grid grid-2">
              <div className="form-row">
                <label>Category</label>
                <select value={newNode.category_id} onChange={(e) => setNewNode({ ...newNode, category_id: e.target.value, parent_id: '' })} required>
                  <option value="">Select category</option>
                  {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
              <div className="form-row">
                <label>Parent Node (optional)</label>
                <select value={newNode.parent_id} onChange={(e) => setNewNode({ ...newNode, parent_id: e.target.value })}>
                  <option value="">None (top-level)</option>
                  {nodesInCategory.map((n) => <option key={n.id} value={n.id}>{n.name}</option>)}
                </select>
              </div>
              <div className="form-row">
                <label>Node Code</label>
                <input type="text" value={newNode.code} onChange={(e) => setNewNode({ ...newNode, code: e.target.value })} placeholder="e.g. NR-1-5" required />
              </div>
              <div className="form-row">
                <label>Node Name</label>
                <input type="text" value={newNode.name} onChange={(e) => setNewNode({ ...newNode, name: e.target.value })} required />
              </div>
            </div>
            <div className="form-row">
              <label>Description</label>
              <textarea value={newNode.description} onChange={(e) => setNewNode({ ...newNode, description: e.target.value })} rows={2} />
            </div>
            <button className="btn" type="submit">Add Node</button>
            <p style={{ fontSize: 12, color: '#6b7280', marginTop: 10 }}>
              Framework changes are versioned — existing completed assessment results are unaffected by edits made here.
            </p>
          </form>

          <div className="card">
            <table>
              <thead><tr><th>Category</th><th>Code</th><th>Name</th><th>Parent</th><th>Active</th><th></th></tr></thead>
              <tbody>
                {nodes.map((n) => (
                  <tr key={n.id}>
                    <td>{categories.find((c) => c.id === n.category_id)?.name}</td>
                    <td>{n.code}</td>
                    <td>{n.name}</td>
                    <td>{nodes.find((p) => p.id === n.parent_id)?.name || '—'}</td>
                    <td>{n.is_active ? 'Yes' : 'No'}</td>
                    <td>
                      <button className="btn secondary" style={{ padding: '4px 10px', fontSize: 12 }} onClick={() => toggleNodeActive(n)}>
                        {n.is_active ? 'Disable' : 'Enable'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {tab === 'users' && (
        <>
          <form className="card" onSubmit={handleCreateUser} style={{ marginBottom: 20 }}>
            <h3 style={{ marginTop: 0, fontSize: 15 }}>Add User</h3>
            <div className="grid grid-4">
              <div className="form-row"><label>Full Name</label><input type="text" value={newUser.full_name} onChange={(e) => setNewUser({ ...newUser, full_name: e.target.value })} required /></div>
              <div className="form-row"><label>Email</label><input type="email" value={newUser.email} onChange={(e) => setNewUser({ ...newUser, email: e.target.value })} required /></div>
              <div className="form-row"><label>Password</label><input type="password" value={newUser.password} onChange={(e) => setNewUser({ ...newUser, password: e.target.value })} required /></div>
              <div className="form-row">
                <label>Role</label>
                <select value={newUser.role} onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}>
                  <option value="ADMIN">Admin</option>
                  <option value="ASSESSOR">Assessor</option>
                  <option value="REVIEWER">Reviewer</option>
                </select>
              </div>
            </div>
            <button className="btn" type="submit">Create User</button>
          </form>

          <div className="card">
            <table>
              <thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Active</th></tr></thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id}><td>{u.full_name}</td><td>{u.email}</td><td>{u.role}</td><td>{u.is_active ? 'Yes' : 'No'}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}
