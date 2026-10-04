import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createProfile, cvPrefill, getProfile } from '../api/profile'
import BackButton from '../components/BackButton'

const QUESTIONS = [
  ['target_role', 'What role are you targeting?'],
  ['current_skills', 'What are your main technical and professional skills?'],
  ['background', 'What is your educational or professional background?'],
  ['experience', 'How many years of relevant experience do you have?'],
  ['tools', 'What tools, languages, or platforms do you use regularly?'],
  ['location', 'Where are you based, and are you open to relocation or remote work?'],
  ['salary', 'What is your target salary range?'],
  ['open_to_learning', 'Are there areas you are actively trying to develop or learn?'],
  ['timeline', 'What is your job search timeline?'],
  ['self_gaps', 'What do you feel are your biggest gaps for the role you are targeting?'],
  ['access_needs', 'Do you have any disabilities or access needs we should be aware of?'],
]

const CV_EXTRACTABLE_KEYS = new Set(QUESTIONS.slice(0, 6).map(([key]) => key))

function ProgressBar({ pct }) {
  return (
    <div className="w-full h-2 bg-mint-border rounded-full overflow-hidden mb-8">
      <div className="h-full bg-mint transition-all duration-150" style={{ width: `${pct}%` }} />
    </div>
  )
}

function QuestionCard({ children }) {
  return (
    <div className="bg-white shadow-card border-l-4 border-mint rounded-xl p-6">{children}</div>
  )
}

export default function Onboarding() {
  const navigate = useNavigate()
  const [stage, setStage] = useState('upload')
  const [cvFile, setCvFile] = useState(null)
  const [extracting, setExtracting] = useState(false)
  const [prefillNotice, setPrefillNotice] = useState('')
  const [step, setStep] = useState(0)
  const [answers, setAnswers] = useState({})
  const [prefilledKeys, setPrefilledKeys] = useState(() => new Set())
  const [current, setCurrent] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [hasExistingProfile, setHasExistingProfile] = useState(false)

  const [key, question] = QUESTIONS[step]

  useEffect(() => {
    getProfile()
      .then(() => setHasExistingProfile(true))
      .catch(() => setHasExistingProfile(false))
  }, [])

  useEffect(() => {
    // Only re-syncs on step change, not on every keystroke or answers update mid-step.
    setCurrent(answers[QUESTIONS[step][0]] || '')
  }, [step])

  async function handleContinueFromUpload() {
    if (!cvFile) {
      setStage('questions')
      return
    }
    setExtracting(true)
    try {
      const extracted = await cvPrefill(cvFile)
      const filled = Object.fromEntries(
        Object.entries(extracted || {}).filter(([, value]) => (value || '').trim())
      )
      if (Object.keys(filled).length > 0) {
        setAnswers((prev) => ({ ...prev, ...filled }))
        setPrefilledKeys(new Set(Object.keys(filled)))
        setPrefillNotice("We've pre-filled what we could find from your CV. Check it over and adjust anything that's wrong.")
      }
    } catch {
      // CV extraction is a convenience only, never blocks onboarding
    } finally {
      setExtracting(false)
      setStage('questions')
    }
  }

  async function finish(finalAnswers) {
    setSubmitting(true)
    try {
      await createProfile(finalAnswers)
      navigate('/dashboard')
    } catch {
      setError('Could not save your profile. Try again.')
      setSubmitting(false)
    }
  }

  function handleNext() {
    if (!current.trim()) {
      setError('Please enter an answer before continuing.')
      return
    }
    setError('')
    advance(current.trim())
  }

  function handleSkip() {
    setError('')
    advance('')
  }

  function advance(value) {
    const updated = { ...answers, [key]: value }
    setAnswers(updated)
    if (step + 1 >= QUESTIONS.length) {
      finish(updated)
    } else {
      setStep(step + 1)
    }
  }

  function handleTextareaKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleNext()
    }
  }

  if (stage === 'upload') {
    return (
      <div className="min-h-screen bg-gray-50 px-4 py-10">
        <div className="max-w-[720px] mx-auto">
          {hasExistingProfile && <BackButton />}
          <QuestionCard>
            <p className="text-xs uppercase tracking-wide text-mint font-semibold">Speed things up</p>
            <h2 className="text-lg font-bold text-teal mt-2">Upload your CV</h2>
            <p className="text-body text-sm mt-1">
              Upload your CV and we'll pre-fill what we can, so you only have to answer what's left.
            </p>

            <label className="mt-4 block border-2 border-dashed border-mint-border bg-mint-light rounded-xl p-8 text-center cursor-pointer">
              <span className="text-3xl block mb-2">&#8593;</span>
              <span className="text-body text-sm">{cvFile ? cvFile.name : 'Upload your CV (PDF)'}</span>
              <input
                type="file"
                accept="application/pdf"
                className="hidden"
                disabled={extracting}
                onChange={(e) => setCvFile(e.target.files?.[0] || null)}
              />
            </label>

            <div className="mt-4 flex gap-3">
              <button
                type="button"
                onClick={handleContinueFromUpload}
                disabled={extracting}
                className="flex-1 bg-mint text-teal rounded-lg py-2.5 font-medium disabled:opacity-50 transition-colors duration-150"
              >
                {extracting ? 'Reading your CV...' : 'Continue'}
              </button>
              <button
                type="button"
                onClick={() => setStage('questions')}
                disabled={extracting}
                className="flex-1 border border-mint-border text-teal bg-white rounded-lg py-2.5 font-medium disabled:opacity-50 transition-colors duration-150"
              >
                Skip
              </button>
            </div>
          </QuestionCard>
        </div>
      </div>
    )
  }

  // step counts completed questions, not the one currently shown, so the bar starts at 0%
  // (not 1/11) and only reaches 100% once the last question has been answered and submitted.
  const progressPct = (step / QUESTIONS.length) * 100
  const isPrefilled = prefilledKeys.has(key)

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-10">
      <div className="max-w-[720px] mx-auto">
        {hasExistingProfile && <BackButton />}
        <ProgressBar pct={progressPct} />

        <QuestionCard>
          <p className="text-xs uppercase tracking-wide text-mint font-semibold text-right">
            Question {step + 1} of {QUESTIONS.length}
          </p>
          <div className="flex items-center gap-2 mt-2">
            <h2 className="text-lg font-bold text-teal">{question}</h2>
            {isPrefilled && (
              <span className="shrink-0 bg-mint-light text-teal text-[10px] font-semibold uppercase tracking-wide px-2 py-0.5 rounded-full border border-mint">
                Pre-filled
              </span>
            )}
          </div>

          {prefillNotice && CV_EXTRACTABLE_KEYS.has(key) && (
            <p className="text-xs text-gray-500 mt-2">{prefillNotice}</p>
          )}

          {error && <p className="text-sm text-red-600 mt-2">{error}</p>}

          <div className={isPrefilled ? 'mt-4 border-l-[3px] border-mint rounded-r-lg overflow-hidden' : 'mt-4'}>
            <textarea
              value={current}
              onChange={(e) => setCurrent(e.target.value)}
              onKeyDown={handleTextareaKeyDown}
              rows={5}
              className={`w-full bg-gray-50 border border-mint-border px-4 py-3 text-body focus:outline-none focus:border-mint ${
                isPrefilled ? 'rounded-r-lg' : 'rounded-lg'
              }`}
              disabled={submitting}
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">Press Enter to continue, Shift+Enter for a new line.</p>

          <div className="mt-4 flex gap-3">
            <button
              type="button"
              onClick={handleNext}
              disabled={submitting}
              className="flex-1 bg-mint text-teal rounded-lg py-2.5 font-medium disabled:opacity-50 transition-colors duration-150"
            >
              {submitting ? 'Saving...' : 'Next'}
            </button>
            <button
              type="button"
              onClick={handleSkip}
              disabled={submitting}
              className="flex-1 border border-mint-border text-teal bg-white rounded-lg py-2.5 font-medium disabled:opacity-50 transition-colors duration-150"
            >
              Skip
            </button>
          </div>
        </QuestionCard>
      </div>
    </div>
  )
}
