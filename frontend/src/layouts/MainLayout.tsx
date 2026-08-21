import React from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function MainLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  const links = [
    { to: '/', label: 'Dashboard' },
    { to: '/assessments', label: 'Assessments' },
    { to: '/tree', label: 'LINDDUN Tree' },
    { to: '/questions', label: 'Questions', adminOnly: true },
    { to: '/admin', label: 'Admin', adminOnly: true },
    { to: '/audit-logs', label: 'Audit Logs', adminOnly: true },
  ]

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h1>LINDDUN Platform</h1>
        <nav>
          {links
            .filter((l) => !l.adminOnly || user?.role === 'ADMIN')
            .map((l) => (
              <NavLink key={l.to} to={l.to} end={l.to === '/'} className={({ isActive }) => (isActive ? 'active' : '')}>
                {l.label}
              </NavLink>
            ))}
        </nav>
        <div className="user-box">
          <div>{user?.full_name}</div>
          <div>{user?.role}</div>
          <button className="logout-btn" onClick={handleLogout}>Log out</button>
        </div>
      </aside>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}
