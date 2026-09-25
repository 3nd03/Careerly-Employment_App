import { useState } from 'react'
import Layout from '../components/Layout'
import Card from '../components/Card'
import BackButton from '../components/BackButton'
import FollowUpChat from '../components/FollowUpChat'
import { runTailoredCv } from '../api/tools'
import { markToolUsed } from '../utils/toolActivity'

export default function TailoredCvBuilder() {
  const [jobDescription, setJobDescription] = useState('')
  const [cvText, setCvText] = useState('')
  const [result, setResult] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleGenerate() {
    if (!jobDescription.trim()) {
      setError('Paste the job description above before generating.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const { result: cv } = await runTailoredCv(jobDescription.trim(), cvText.trim())
      setResult(cv)
      markToolUsed('tailored_cv')
    } catch {
      setError('Could not generate the CV. Try again.')
    } finally {
      setLoading(false)
    }
  }

  function handleDownload() {
    window.print()
  }

  return (
    <Layout>
      <style>{`
        @media print {
          body * { visibility: hidden; }
          #tailored-cv-preview, #tailored-cv-preview * { visibility: visible; }
          #tailored-cv-preview {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
          }
        }
      `}</style>

      <div className="print:hidden">
        <BackButton />
      </div>

      <Card className="print:hidden">
        <h1 className="text-2xl font-bold text-teal mb-6">Tailored CV Builder</h1>

        <label className="text-[11px] uppercase tracking-wide text-label">Job description</label>
        <textarea
          rows={8}
          value={jobDescription}
          onChange={(e) => setJobDescription(e.target.value)}
          className="mt-1 w-full bg-white border border-card-border rounded-[10px] px-4 py-3 text-sm text-body focus:outline-none focus:border-mint transition-colors duration-200"
        />

        <label className="text-[11px] uppercase tracking-wide text-label mt-4 block">
          Existing CV text (optional)
        </label>
        <p className="text-xs text-gray-500 mt-1 mb-1">Leave blank to use your profile only.</p>
        <textarea
          rows={8}
          value={cvText}
          onChange={(e) => setCvText(e.target.value)}
          className="w-full bg-white border border-card-border rounded-[10px] px-4 py-3 text-sm text-body focus:outline-none focus:border-mint transition-colors duration-200"
        />

        <button
          type="button"
          onClick={handleGenerate}
          disabled={loading}
          className="w-full h-12 bg-mint text-teal rounded-[10px] font-medium mt-4 disabled:opacity-50 hover:brightness-90 transition-all duration-200"
        >
          {loading ? 'Generating...' : 'Generate tailored CV'}
        </button>

        {error && <p className="text-sm text-red-600 mt-4">{error}</p>}
      </Card>

      {result && (
        <>
          <Card className="mt-6 print:hidden">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-bold text-teal text-sm">Your Tailored CV</h2>
              <button
                type="button"
                onClick={handleDownload}
                className="bg-mint text-teal rounded-[10px] px-4 py-2 text-sm font-medium hover:brightness-90 transition-all duration-200"
              >
                Download as PDF
              </button>
            </div>
            <div id="tailored-cv-preview" className="bg-white border-l-[3px] border-mint rounded-r-lg p-4">
              <p className="text-body text-sm whitespace-pre-line">{result}</p>
            </div>
          </Card>
          <div className="print:hidden">
            <Card className="mt-6">
              <FollowUpChat toolName="tailored_cv" result={result} />
            </Card>
          </div>
        </>
      )}
    </Layout>
  )
}
