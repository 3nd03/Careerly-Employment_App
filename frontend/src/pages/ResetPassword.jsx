import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { resetPassword } from '../api/auth'

export default function ResetPassword() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token') || ''
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')

    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    setLoading(true)
    try {
      await resetPassword(token, newPassword)
      navigate('/login', { state: { message: 'Your password has been reset. Log in with your new password.' } })
    } catch (err) {
      setError(typeof err.response?.data?.detail === 'string'
          ? 'This reset link is invalid or has expired. Request a new one.'
          : 'Could not reset the password. Try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-white flex items-center justify-center px-4">
      <div className="w-full max-w-[440px] bg-mint-light border border-mint-border rounded-xl p-6">
        <h1 className="text-2xl font-bold text-teal text-center">Careerly</h1>
        <div className="border-t border-mint my-6" />

        <h2 className="text-xl font-bold text-teal">Set a new password</h2>
        {!token ? (
          <p className="text-body text-sm mt-1">
            This page needs the link from your password reset email.{' '}
            <Link to="/forgot-password" className="text-teal font-medium">
              Request a new link
            </Link>
            .
          </p>
        ) : (
          <>
            <p className="text-body text-sm mt-1 mb-6">Choose a new password for your account.</p>

            {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="text-xs uppercase tracking-wide text-label">New password</label>
                <input
                  type="password"
                  required
                  minLength={8}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="mt-1 w-full bg-white border border-mint-border rounded-lg px-4 py-2 text-body focus:outline-none focus:border-mint"
                />
              </div>
              <div>
                <label className="text-xs uppercase tracking-wide text-label">Confirm new password</label>
                <input
                  type="password"
                  required
                  minLength={8}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="mt-1 w-full bg-white border border-mint-border rounded-lg px-4 py-2 text-body focus:outline-none focus:border-mint"
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-mint text-teal rounded-lg py-2.5 font-medium disabled:opacity-50"
              >
                {loading ? 'Resetting...' : 'Reset password'}
              </button>
            </form>
          </>
        )}

        <p className="text-center text-sm text-body mt-6">
          <Link to="/login" className="text-teal font-medium">
            Back to log in
          </Link>
        </p>
      </div>
    </div>
  )
}
