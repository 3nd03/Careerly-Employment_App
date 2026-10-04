import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { signup } from '../api/auth'

export default function Signup() {
  const navigate = useNavigate()
  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [consent, setConsent] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')

    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }
    if (!consent) {
      setError('You must agree to the Privacy Policy to create an account.')
      return
    }

    setLoading(true)
    try {
      const { access_token } = await signup({ email, password, display_name: displayName, consent })
      localStorage.setItem('token', access_token)
      localStorage.setItem('email', email.trim().toLowerCase())
      if (displayName.trim()) {
        localStorage.setItem('display_name', displayName.trim())
      }
      navigate('/onboarding')
    } catch (err) {
      const detail = err.response?.data?.detail
      if (typeof detail === 'string') {
        setError(detail)
      } else if (Array.isArray(detail) && detail.some((d) => d.loc?.includes('email'))) {
        setError('Please enter a valid email address.')
      } else {
        setError('Could not create an account.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-white flex items-center justify-center px-4">
      <div className="w-full max-w-[440px] bg-mint-light border border-mint-border rounded-xl p-6">
        <h1 className="text-2xl font-bold text-teal text-center">Careerly</h1>
        <div className="border-t border-mint my-6" />

        <h2 className="text-xl font-bold text-teal">Create an account</h2>
        <p className="text-body text-sm mt-1 mb-6">A few details and you're in.</p>

        {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-xs uppercase tracking-wide text-label">Name</label>
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              className="mt-1 w-full bg-white border border-mint-border rounded-lg px-4 py-2 text-body focus:outline-none focus:border-mint"
            />
          </div>
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
          <div>
            <label className="text-xs uppercase tracking-wide text-label">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full bg-white border border-mint-border rounded-lg px-4 py-2 text-body focus:outline-none focus:border-mint"
            />
          </div>
          <div>
            <label className="text-xs uppercase tracking-wide text-label">Confirm password</label>
            <input
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="mt-1 w-full bg-white border border-mint-border rounded-lg px-4 py-2 text-body focus:outline-none focus:border-mint"
            />
          </div>
          <label className="flex items-start gap-2 text-sm text-body">
            <input
              type="checkbox"
              checked={consent}
              onChange={(e) => setConsent(e.target.checked)}
              className="mt-0.5"
            />
            <span>
              I agree to the{' '}
              <Link to="/privacy-policy" target="_blank" className="text-teal font-medium underline">
                Privacy Policy
              </Link>
            </span>
          </label>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-mint text-teal rounded-lg py-2.5 font-medium disabled:opacity-50"
          >
            {loading ? 'Signing up...' : 'Sign up'}
          </button>
        </form>

        <p className="text-center text-sm text-body mt-6">
          Already have an account?{' '}
          <Link to="/login" className="text-teal font-medium">
            Log in
          </Link>
        </p>
      </div>
    </div>
  )
}
