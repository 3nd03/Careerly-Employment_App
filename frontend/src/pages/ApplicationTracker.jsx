import { useEffect, useState } from 'react'
import Layout from '../components/Layout'
import Card from '../components/Card'
import BackButton from '../components/BackButton'
import { getApplications, addApplication, updateApplicationStatus, deleteApplication } from '../api/tools'
import { markToolUsed } from '../utils/toolActivity'

const STATUS_OPTIONS = ['Applied', 'Interview', 'Offer', 'Rejected']
const FILTER_OPTIONS = ['All', ...STATUS_OPTIONS]
const SORT_OPTIONS = [
  { value: 'date_desc', label: 'Date applied (newest first)' },
  { value: 'date_asc', label: 'Date applied (oldest first)' },
]

export default function ApplicationTracker() {
  const [applications, setApplications] = useState([])
  const [company, setCompany] = useState('')
  const [role, setRole] = useState('')
  const [dateApplied, setDateApplied] = useState('')
  const [status, setStatus] = useState('Applied')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [statusFilter, setStatusFilter] = useState('All')
  const [sortOrder, setSortOrder] = useState('date_desc')

  useEffect(() => {
    refresh()
  }, [])

  function refresh() {
    getApplications()
      .then((data) => {
        setApplications(data)
        if (data.length > 0) markToolUsed('application_tracker')
      })
      .catch(() => {})
  }

  async function handleAdd(e) {
    e.preventDefault()
    if (!company.trim() || !role.trim() || !dateApplied) {
      setError('Fill in company, role, and date before adding.')
      return
    }
    setError('')
    setSubmitting(true)
    try {
      await addApplication({ company: company.trim(), role: role.trim(), date_applied: dateApplied, status })
      setCompany('')
      setRole('')
      setDateApplied('')
      setStatus('Applied')
      markToolUsed('application_tracker')
      refresh()
    } catch {
      setError('Could not add the application.')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleStatusChange(applicationId, newStatus) {
    setApplications((prev) => prev.map((a) => (a.id === applicationId ? { ...a, status: newStatus } : a)))
    try {
      await updateApplicationStatus(applicationId, newStatus)
    } catch {
      refresh()
    }
  }

  async function handleDelete(applicationId) {
    const previous = applications
    setApplications((prev) => prev.filter((a) => a.id !== applicationId))
    try {
      await deleteApplication(applicationId)
    } catch {
      setApplications(previous)
    }
  }

  const visibleApplications = applications
    .filter((a) => statusFilter === 'All' || a.status === statusFilter)
    .sort((a, b) => {
      const diff = new Date(a.date_applied) - new Date(b.date_applied)
      return sortOrder === 'date_asc' ? diff : -diff
    })

  return (
    <Layout>
      <BackButton />
      <Card>
        <h1 className="text-2xl font-bold text-teal mb-6">Application Tracker</h1>

        <form onSubmit={handleAdd} className="bg-white border-l-[3px] border-mint rounded-r-lg p-5 space-y-4">
          <h2 className="font-bold text-teal text-sm">Add an application</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-[11px] uppercase tracking-wide text-label">Company</label>
              <input
                type="text"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                className="mt-1 w-full bg-white border border-card-border rounded-[10px] px-4 py-2.5 text-sm text-body focus:outline-none focus:border-mint transition-colors duration-200"
              />
            </div>
            <div>
              <label className="text-[11px] uppercase tracking-wide text-label">Role</label>
              <input
                type="text"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="mt-1 w-full bg-white border border-card-border rounded-[10px] px-4 py-2.5 text-sm text-body focus:outline-none focus:border-mint transition-colors duration-200"
              />
            </div>
            <div>
              <label className="text-[11px] uppercase tracking-wide text-label">Date applied</label>
              <input
                type="date"
                value={dateApplied}
                onChange={(e) => setDateApplied(e.target.value)}
                className="mt-1 w-full bg-white border border-card-border rounded-[10px] px-4 py-2.5 text-sm text-body focus:outline-none focus:border-mint transition-colors duration-200"
              />
            </div>
            <div>
              <label className="text-[11px] uppercase tracking-wide text-label">Status</label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="mt-1 w-full bg-white border border-card-border rounded-[10px] px-4 py-2.5 text-sm text-body focus:outline-none focus:border-mint transition-colors duration-200"
              >
                {STATUS_OPTIONS.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button
            type="submit"
            disabled={submitting}
            className="h-12 px-6 bg-mint text-teal rounded-[10px] font-medium disabled:opacity-50 hover:brightness-90 transition-all duration-200"
          >
            {submitting ? 'Adding...' : 'Add application'}
          </button>
        </form>

        <div className="mt-6 flex flex-wrap gap-3 items-end">
          <div>
            <label className="text-[11px] uppercase tracking-wide text-label">Filter by status</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="mt-1 bg-white border border-card-border rounded-[10px] px-3 py-2 text-sm text-body focus:outline-none focus:border-mint transition-colors duration-200"
            >
              {FILTER_OPTIONS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-[11px] uppercase tracking-wide text-label">Sort by</label>
            <select
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value)}
              className="mt-1 bg-white border border-card-border rounded-[10px] px-3 py-2 text-sm text-body focus:outline-none focus:border-mint transition-colors duration-200"
            >
              {SORT_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="mt-4 overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="text-left text-[11px] uppercase tracking-wide text-label border-b border-card-border">
                <th className="py-2 pr-4">Company</th>
                <th className="py-2 pr-4">Role</th>
                <th className="py-2 pr-4">Date applied</th>
                <th className="py-2 pr-4">Status</th>
                <th className="py-2"></th>
              </tr>
            </thead>
            <tbody>
              {visibleApplications.map((app) => (
                <tr key={app.id} className="border-b border-gray-100">
                  <td className="py-3 pr-4 text-body text-sm">{app.company}</td>
                  <td className="py-3 pr-4 text-body text-sm">{app.role}</td>
                  <td className="py-3 pr-4 text-body text-sm">{app.date_applied}</td>
                  <td className="py-3 pr-4">
                    <select
                      value={app.status}
                      onChange={(e) => handleStatusChange(app.id, e.target.value)}
                      className="bg-white border border-card-border rounded-[10px] px-3 py-1.5 text-body text-sm focus:outline-none focus:border-mint transition-colors duration-200"
                    >
                      {STATUS_OPTIONS.map((s) => (
                        <option key={s} value={s}>
                          {s}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="py-3">
                    <button
                      type="button"
                      onClick={() => handleDelete(app.id)}
                      className="text-red-600 text-sm hover:underline"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {applications.length === 0 && (
            <p className="text-body text-sm mt-4">No applications tracked yet. Add one above.</p>
          )}
          {applications.length > 0 && visibleApplications.length === 0 && (
            <p className="text-body text-sm mt-4">No applications match this filter.</p>
          )}
        </div>
      </Card>
    </Layout>
  )
}
