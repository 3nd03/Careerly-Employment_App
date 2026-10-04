import { useState } from 'react'
import { Link } from 'react-router-dom'
import { forgotPassword } from '../api/auth'

export default function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setMessage('')
    setLoading(true)
    try {
      await forgotPassword(email.trim().toLowerCase())
      setMessage(
        "If that email is registered, we've sent a link to reset your password. It expires in 1 hour, so check your inbox (and spam folder)."
      )
    } catch {
      setError('Could not process that request. Try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-white flex items-center justify-center px-4">
      <div className="w-full max-w-[440px] bg-mint-light border border-mint-border rounded-xl p-6">
        <h1 className="text-2xl font-bold text-teal text-center">Careerly</h1>
        <div className="border-t border-mint my-6" />

        <h2 className="text-xl font-bold text-teal">Reset your password</h2>
        <p className="text-body text-sm mt-1 mb-6">
          Enter your account email and we'll send you a reset link.
        </p>

        {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

        {message ? (
          <div>
            <p className="text-sm text-body">{message}</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs uppercase tracking-wide text-label">Email</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 w-full bg-white border border-mint-border rounded-lg px-4 py-2 text-body focus:outline-none focus:border-mint"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-mint text-teal rounded-lg py-2.5 font-medium disabled:opacity-50"
            >
              {loading ? 'Sending...' : 'Send reset link'}
            </button>
          </form>
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
