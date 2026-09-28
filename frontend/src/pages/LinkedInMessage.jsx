import { useState } from 'react'
import Layout from '../components/Layout'
import Card from '../components/Card'
import BackButton from '../components/BackButton'
import FollowUpChat from '../components/FollowUpChat'
import { runLinkedInMessage } from '../api/tools'
import { markToolUsed } from '../utils/toolActivity'

export default function LinkedInMessage() {
  const [context, setContext] = useState('')
  const [result, setResult] = useState('')
  const [loading, setLoading] = useState(false)
  const [copied, setCopied] = useState(false)

  async function handleGenerate() {
    setLoading(true)
    try {
      const { message_text } = await runLinkedInMessage(context.trim())
      setResult(message_text)
      markToolUsed('linkedin_message')
    } finally {
      setLoading(false)
    }
  }

  function handleCopy() {
    navigator.clipboard.writeText(result)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <Layout>
      <BackButton />
      <Card>
        <h1 className="text-2xl font-bold text-teal mb-6">LinkedIn Message Generator</h1>

        <label className="text-[11px] uppercase tracking-wide text-label">
          Who are you reaching out to? (optional)
        </label>
        <textarea
          rows={5}
          value={context}
          onChange={(e) => setContext(e.target.value)}
          placeholder="e.g. hiring manager at a specific company, alumnus in your target field"
          className="mt-1 w-full bg-white border border-card-border rounded-[10px] px-4 py-3 text-sm text-body focus:outline-none focus:border-mint transition-colors duration-200"
        />

        <button
          type="button"
          onClick={handleGenerate}
          disabled={loading}
          className="w-full h-12 bg-mint text-teal rounded-[10px] font-medium mt-4 disabled:opacity-50 hover:brightness-90 transition-all duration-200"
        >
          {loading ? 'Writing...' : 'Generate message'}
        </button>

        {result && (
          <>
            <div className="mt-6 bg-white border-l-[3px] border-mint rounded-r-lg p-4 relative">
              <button
                type="button"
                onClick={handleCopy}
                className="absolute top-4 right-4 border border-card-border text-teal bg-white rounded-[10px] px-3 py-1 text-sm transition-colors duration-200"
              >
                {copied ? 'Copied' : 'Copy'}
              </button>
              <h3 className="font-bold text-teal mb-1 text-sm">Your Message</h3>
              <p className="text-body text-sm whitespace-pre-line pr-16">{result}</p>
              <p className={`text-xs mt-2 ${result.length > 300 ? 'text-red-600' : 'text-gray-500'}`}>
                {result.length} / 300 characters
              </p>
            </div>
            <FollowUpChat toolName="linkedin_message" result={result} />
          </>
        )}
      </Card>
    </Layout>
  )
}
