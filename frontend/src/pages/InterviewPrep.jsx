import { useState } from 'react'
import Layout from '../components/Layout'
import Card from '../components/Card'
import BackButton from '../components/BackButton'
import FollowUpChat from '../components/FollowUpChat'
import { runInterviewPrep, runInterviewFeedback } from '../api/tools'
import { markToolUsed } from '../utils/toolActivity'

function parseQuestions(text) {
  if (!text) return []
  const blocks = [...text.matchAll(/(?:^|\n)\s*\d+\.\s*([\s\S]*?)(?=\n\s*\d+\.\s|$)/g)].map((m) => m[1].trim())
  return blocks.map((block) => {
    const markerIndex = block.search(/Strong answer covers:/i)
    if (markerIndex === -1) {
      return { question: block, guidance: '' }
    }
    return {
      question: block.slice(0, markerIndex).trim(),
      guidance: block.slice(markerIndex).replace(/Strong answer covers:/i, '').trim(),
    }
  })
}

function AnswerFeedback({ entry, onAnswerChange, onGetFeedback }) {
  return (
    <div className="mt-3 pt-3 border-t border-gray-100">
      <label className="text-[11px] uppercase tracking-wide text-label">Your answer</label>
      <textarea
        rows={4}
        value={entry.answer}
        onChange={(e) => onAnswerChange(e.target.value)}
        className="mt-1 w-full bg-white border border-card-border rounded-[10px] px-3 py-2 text-sm text-body focus:outline-none focus:border-mint transition-colors duration-200"
      />
      <button
        type="button"
        onClick={onGetFeedback}
        disabled={entry.loading || !entry.answer.trim()}
        className="mt-2 border border-card-border text-teal bg-white rounded-[10px] px-4 py-1.5 text-sm disabled:opacity-50 transition-colors duration-200"
      >
        {entry.loading ? 'Getting feedback...' : 'Get feedback'}
      </button>
      {entry.feedback && (
        <div className="mt-3 bg-mint-light rounded-lg p-3 text-body text-sm whitespace-pre-line">
          {entry.feedback}
        </div>
      )}
    </div>
  )
}

export default function InterviewPrep() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [answers, setAnswers] = useState({})
  const skillGapDone = sessionStorage.getItem('skill_gap_done') === '1'

  async function handleGenerate() {
    setLoading(true)
    try {
      const { result: text } = await runInterviewPrep()
      setResult(text)
      setAnswers({})
      markToolUsed('interview_prep')
    } finally {
      setLoading(false)
    }
  }

  function setAnswerText(index, value) {
    setAnswers((prev) => ({
      ...prev,
      [index]: { answer: value, feedback: prev[index]?.feedback || '', loading: false },
    }))
  }

  async function getFeedback(index, question) {
    const entry = answers[index] || { answer: '', feedback: '' }
    if (!entry.answer.trim()) return
    setAnswers((prev) => ({ ...prev, [index]: { ...entry, loading: true } }))
    try {
      const { feedback } = await runInterviewFeedback(question, entry.answer.trim())
      setAnswers((prev) => ({ ...prev, [index]: { ...prev[index], feedback, loading: false } }))
    } catch {
      setAnswers((prev) => ({
        ...prev,
        [index]: { ...prev[index], feedback: 'Could not get feedback. Try again.', loading: false },
      }))
    }
  }

  const questions = result ? parseQuestions(result) : []

  return (
    <Layout>
      <BackButton />
      <Card>
        <h1 className="text-2xl font-bold text-teal mb-6">Interview Prep</h1>

        {!skillGapDone && (
          <div className="bg-white border-l-[3px] border-mint rounded-r-lg p-4 mb-4 text-body text-sm">
            Tip: run the Skill Gap Analysis first for questions targeted at your weaker areas.
          </div>
        )}

        <button
          type="button"
          onClick={handleGenerate}
          disabled={loading}
          className="w-full h-12 bg-mint text-teal rounded-[10px] font-medium disabled:opacity-50 hover:brightness-90 transition-all duration-200"
        >
          {loading ? 'Preparing...' : 'Generate questions'}
        </button>

        {questions.length > 0 && (
          <>
            <div className="mt-6 space-y-3">
              {questions.map((q, i) => (
                <div key={i} className="bg-white border-l-[3px] border-mint rounded-r-lg p-4">
                  <div className="flex gap-3 items-start">
                    <span className="w-6 h-6 shrink-0 rounded-full bg-mint text-teal font-bold flex items-center justify-center text-xs">
                      {i + 1}
                    </span>
                    <div className="flex-1">
                      <p className="font-bold text-teal text-sm">{q.question}</p>
                      {q.guidance && <p className="text-body text-sm mt-1">{q.guidance}</p>}
                    </div>
                  </div>
                  <AnswerFeedback
                    entry={answers[i] || { answer: '', feedback: '', loading: false }}
                    onAnswerChange={(value) => setAnswerText(i, value)}
                    onGetFeedback={() => getFeedback(i, q.question)}
                  />
                </div>
              ))}
            </div>
            <FollowUpChat toolName="interview_prep" result={result} />
          </>
        )}
      </Card>
    </Layout>
  )
}
