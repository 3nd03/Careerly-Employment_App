import { useState } from 'react'
import Layout from '../components/Layout'
import Card from '../components/Card'
import BackButton from '../components/BackButton'
import FollowUpChat from '../components/FollowUpChat'
import { runCoverLetter } from '../api/tools'
import { markToolUsed } from '../utils/toolActivity'

const TONES = ['Formal', 'Warm', 'Direct']

export default function CoverLetter() {
  const [jobDescription, setJobDescription] = useState('')
  const [tone, setTone] = useState('Formal')
  const [result, setResult] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)

  async function handleGenerate() {
    if (!jobDescription.trim()) {
      setError('Paste a job description above before generating.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const { letter_text } = await runCoverLetter(jobDescription.trim(), tone)
      setResult(letter_text)
      markToolUsed('cover_letter')
    } catch {
      setError('Could not generate the cover letter. Try again.')
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
        <h1 className="text-2xl font-bold text-teal mb-6">Cover Letter Generator</h1>

        <label className="text-[11px] uppercase tracking-wide text-label">Job description</label>
        <textarea
          rows={8}
          value={jobDescription}
          onChange={(e) => setJobDescription(e.target.value)}
          className="mt-1 w-full bg-white border border-card-border rounded-[10px] px-4 py-3 text-sm text-body focus:outline-none focus:border-mint transition-colors duration-200"
        />

        <label className="text-[11px] uppercase tracking-wide text-label mt-4 block">Tone</label>
        <div className="mt-1 flex gap-2">
          {TONES.map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setTone(t)}
              className={`px-4 py-2 rounded-[10px] text-sm font-medium transition-colors duration-200 ${
                tone === t ? 'bg-mint text-teal' : 'bg-white border border-card-border text-gray-500 hover:bg-mint-light'
              }`}
            >
              {t}
            </button>
          ))}
        </div>

        <button
          type="button"
          onClick={handleGenerate}
          disabled={loading}
          className="w-full h-12 bg-mint text-teal rounded-[10px] font-medium mt-4 disabled:opacity-50 hover:brightness-90 transition-all duration-200"
        >
          {loading ? 'Writing...' : 'Generate cover letter'}
        </button>

        {error && <p className="text-sm text-red-600 mt-4">{error}</p>}

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
              <h3 className="font-bold text-teal mb-1 text-sm">Your Cover Letter</h3>
              <p className="text-body text-sm whitespace-pre-line pr-16">{result}</p>
            </div>
            <FollowUpChat toolName="cover_letter" result={result} />
          </>
        )}
      </Card>
    </Layout>
  )
}
