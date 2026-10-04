import { useEffect, useRef, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import Card from '../components/Card'
import BackButton from '../components/BackButton'
import {
  getProfile,
  updateProfile,
  getAllProfiles,
  activateProfile,
  renameProfile,
  getProfileHistory,
  uploadAvatar,
  uploadProfileCv,
} from '../api/profile'
import { updateMe, changePassword } from '../api/auth'

const HISTORY_LABELS = {
  skill_gap: 'Skill Gap Analysis',
  cv_analysis: 'CV Analyser',
  cover_letter: 'Cover Letter',
  job_roles: 'Job Role Suggestions',
  linkedin_message: 'LinkedIn Message',
  interview_prep: 'Interview Prep',
  cv_download: 'CV Download',
  career_roadmap: 'Career Roadmap',
  salary_insights: 'Salary Insights',
  tailored_cv: 'Tailored CV Builder',
  cv_translate: 'CV Translator',
}

const HISTORY_PREVIEW_LIMIT = 5

const INPUT_CLASS =
  'mt-1 w-full bg-white border border-card-border rounded-[10px] px-4 py-2.5 text-sm text-body focus:outline-none focus:border-mint transition-colors duration-200'

function formatHistoryContent(content) {
  if (content && typeof content === 'object') {
    return Object.entries(content)
      .filter(([, value]) => value)
      .map(([key, value]) => `${key.replaceAll('_', ' ')}: ${value}`)
      .join('\n')
  }
  return content || ''
}

function historyPreview(content) {
  const text = formatHistoryContent(content)
  const firstLine = text.split('\n').find((line) => line.trim()) || 'No details'
  return firstLine.length > 70 ? `${firstLine.slice(0, 70)}...` : firstLine
}

function HistoryEntryRow({ entryKey, entry, isOpen, onToggle }) {
  return (
    <div className="border-t border-gray-100 first:border-t-0">
      <button
        type="button"
        onClick={() => onToggle(entryKey)}
        className="w-full flex items-center gap-3 px-2 py-2 text-left rounded-lg hover:bg-mint-light transition-colors duration-200"
      >
        <span className="text-xs text-gray-500 shrink-0">{new Date(entry.created_at).toLocaleDateString()}</span>
        <span className="flex-1 text-body text-sm truncate">{historyPreview(entry.content)}</span>
        <span className="text-xs text-gray-500 shrink-0">{isOpen ? '▲' : '▼'}</span>
      </button>
      {isOpen && (
        <div className="px-2 pb-3">
          <div className="bg-white border-l-[3px] border-mint rounded-r-lg p-3">
            <p className="text-xs text-gray-500 mb-1">{new Date(entry.created_at).toLocaleString()}</p>
            <p className="text-body text-sm whitespace-pre-line">{formatHistoryContent(entry.content)}</p>
          </div>
        </div>
      )}
    </div>
  )
}

const PROFILE_LABELS = {
  target_role: 'Target role',
  current_skills: 'Current skills',
  background: 'Background',
  experience: 'Experience',
  tools: 'Tools and platforms',
  location: 'Location',
  salary: 'Salary expectations',
  open_to_learning: 'Open to learning',
  timeline: 'Timeline',
  self_gaps: 'Self-identified gaps',
  access_needs: 'Access needs',
}

function Divider() {
  return <div className="border-t border-gray-100 my-8" />
}

function PlaceholderNote({ message }) {
  return <div className="bg-gray-50 rounded-lg p-4 text-body text-sm">{message}</div>
}

export default function Profile() {
  const navigate = useNavigate()
  const location = useLocation()
  const fileInputRef = useRef(null)
  const cvInputRef = useRef(null)
  const [avatarPreview, setAvatarPreview] = useState(null)
  const [avatarUploading, setAvatarUploading] = useState(false)
  const [avatarError, setAvatarError] = useState('')

  const [cvS3Key, setCvS3Key] = useState(null)
  const [cvUploading, setCvUploading] = useState(false)
  const [cvError, setCvError] = useState('')
  const [cvPreview, setCvPreview] = useState('')

  const email = localStorage.getItem('email') || ''
  const [displayName, setDisplayName] = useState(
    () => localStorage.getItem('display_name') || email.split('@')[0] || 'Account'
  )
  const initial = (displayName[0] || '?').toUpperCase()

  const [nameDraft, setNameDraft] = useState(displayName)
  const [savingName, setSavingName] = useState(false)
  const [nameMessage, setNameMessage] = useState('')

  const [passwordFields, setPasswordFields] = useState({ current: '', next: '', confirm: '' })
  const [savingPassword, setSavingPassword] = useState(false)
  const [passwordMessage, setPasswordMessage] = useState({ text: '', isError: false })

  const [fields, setFields] = useState({})
  const [savingProfile, setSavingProfile] = useState(false)
  const [savedMessage, setSavedMessage] = useState('')

  const [allProfiles, setAllProfiles] = useState([])
  const [renameDrafts, setRenameDrafts] = useState({})

  const [history, setHistory] = useState(null)
  const [historyError, setHistoryError] = useState('')
  const [openHistoryTools, setOpenHistoryTools] = useState(() => new Set())
  const [openHistoryEntries, setOpenHistoryEntries] = useState(() => new Set())
  const [expandedHistoryTools, setExpandedHistoryTools] = useState(() => new Set())

  useEffect(() => {
    getProfile()
      .then((data) => {
        setFields(data.data)
        setCvS3Key(data.cv_s3_key || null)
      })
      .catch((err) => {
        if (err.response?.status === 404) navigate('/onboarding')
      })
    refreshProfiles()
    getProfileHistory()
      .then(setHistory)
      .catch(() => setHistoryError('Could not load history.'))
  }, [navigate])

  function toggleHistoryTool(toolKey) {
    setOpenHistoryTools((prev) => {
      const next = new Set(prev)
      if (next.has(toolKey)) {
        next.delete(toolKey)
      } else {
        next.add(toolKey)
      }
      return next
    })
  }

  function toggleHistoryEntry(entryKey) {
    setOpenHistoryEntries((prev) => {
      const next = new Set(prev)
      if (next.has(entryKey)) {
        next.delete(entryKey)
      } else {
        next.add(entryKey)
      }
      return next
    })
  }

  function toggleShowAllHistory(toolKey) {
    setExpandedHistoryTools((prev) => {
      const next = new Set(prev)
      if (next.has(toolKey)) {
        next.delete(toolKey)
      } else {
        next.add(toolKey)
      }
      return next
    })
  }

  useEffect(() => {
    return () => {
      if (avatarPreview) URL.revokeObjectURL(avatarPreview)
    }
  }, [avatarPreview])

  useEffect(() => {
    if (!location.hash) return
    const target = document.getElementById(location.hash.slice(1))
    target?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [location.hash])

  function refreshProfiles() {
    getAllProfiles()
      .then(setAllProfiles)
      .catch(() => {})
  }

  async function handleAvatarPick(e) {
    const file = e.target.files?.[0]
    if (!file) return
    setAvatarError('')
    setAvatarUploading(true)
    try {
      const { avatar_s3_key } = await uploadAvatar(file)
      if (avatarPreview) URL.revokeObjectURL(avatarPreview)
      setAvatarPreview(URL.createObjectURL(file))
      localStorage.setItem('avatar_s3_key', avatar_s3_key)
    } catch {
      setAvatarError('Could not upload avatar. Try again.')
    } finally {
      setAvatarUploading(false)
    }
  }

  async function handleCvPick(e) {
    const file = e.target.files?.[0]
    if (!file) return
    setCvError('')
    setCvPreview('')
    setCvUploading(true)
    try {
      const { cv_text, cv_s3_key } = await uploadProfileCv(file)
      if (!cv_text.trim()) {
        setCvError('Could not extract any text from that PDF. Try a different file.')
      } else {
        setCvS3Key(cv_s3_key)
        setCvPreview(cv_text.slice(0, 100))
      }
    } catch {
      setCvError('Could not upload the CV. Try again.')
    } finally {
      setCvUploading(false)
      e.target.value = ''
    }
  }

  async function handleSaveProfile(e) {
    e.preventDefault()
    setSavingProfile(true)
    setSavedMessage('')
    try {
      const updated = await updateProfile(fields)
      setFields(updated.data)
      setSavedMessage('Profile updated.')
    } catch {
      setSavedMessage('Could not save changes.')
    } finally {
      setSavingProfile(false)
    }
  }

  async function handleSaveName(e) {
    e.preventDefault()
    setNameMessage('')
    if (!nameDraft.trim()) {
      setNameMessage('Enter a name.')
      return
    }
    setSavingName(true)
    try {
      const user = await updateMe(nameDraft.trim())
      localStorage.setItem('display_name', user.display_name)
      setDisplayName(user.display_name)
      setNameDraft(user.display_name)
      setNameMessage('Name updated.')
    } catch {
      setNameMessage('Could not update your name. Try again.')
    } finally {
      setSavingName(false)
    }
  }

  async function handleChangePassword(e) {
    e.preventDefault()
    const { current, next, confirm } = passwordFields
    if (next.length < 8) {
      setPasswordMessage({ text: 'New password must be at least 8 characters.', isError: true })
      return
    }
    if (next !== confirm) {
      setPasswordMessage({ text: 'New passwords do not match.', isError: true })
      return
    }
    setSavingPassword(true)
    setPasswordMessage({ text: '', isError: false })
    try {
      await changePassword(current, next)
      setPasswordFields({ current: '', next: '', confirm: '' })
      setPasswordMessage({ text: 'Password changed. Other devices have been signed out.', isError: false })
    } catch (err) {
      const detail = err.response?.data?.detail
      setPasswordMessage({
        text: typeof detail === 'string' ? detail : 'Could not change your password. Try again.',
        isError: true,
      })
    } finally {
      setSavingPassword(false)
    }
  }

  async function handleSwitch(profileId) {
    await activateProfile(profileId)
    window.location.reload()
  }

  async function handleRename(profileId) {
    const label = renameDrafts[profileId]
    if (!label?.trim()) return
    await renameProfile(profileId, label.trim())
    refreshProfiles()
  }

  return (
    <Layout>
      <BackButton />
      <Card>
        <h1 className="text-2xl font-bold text-teal mb-6">Profile</h1>

        <section>
          <h2 className="font-bold text-teal mb-4 text-sm uppercase tracking-wide">Account</h2>
          <div className="flex items-center gap-5">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={avatarUploading}
              className="w-24 h-24 shrink-0 rounded-full border-2 border-mint bg-mint-light flex items-center justify-center text-teal font-bold text-2xl overflow-hidden disabled:opacity-50"
            >
              {avatarPreview ? (
                <img src={avatarPreview} alt="Avatar preview" className="w-full h-full object-cover" />
              ) : (
                initial
              )}
            </button>
            <input ref={fileInputRef} type="file" accept="image/*" className="hidden" onChange={handleAvatarPick} />
            <div>
              <p className="font-medium text-teal">{displayName}</p>
              <p className="text-sm text-gray-500">{email}</p>
              <p className="text-xs text-gray-500 mt-1">
                {avatarUploading ? 'Uploading...' : 'Click the avatar to upload a new photo.'}
              </p>
              {avatarError && <p className="text-xs text-red-600 mt-1">{avatarError}</p>}
            </div>
          </div>
          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
            <form onSubmit={handleSaveName} className="space-y-3">
              <h3 className="font-bold text-teal text-sm">Name</h3>
              <div>
                <label className="text-xs uppercase tracking-wide text-label">Display name</label>
                <input
                  type="text"
                  value={nameDraft}
                  onChange={(e) => setNameDraft(e.target.value)}
                  maxLength={100}
                  className={INPUT_CLASS}
                />
              </div>
              {nameMessage && <p className="text-sm text-teal">{nameMessage}</p>}
              <button
                type="submit"
                disabled={savingName}
                className="bg-mint text-teal rounded-[10px] px-6 py-2.5 font-medium disabled:opacity-50 hover:brightness-90 transition-all duration-200"
              >
                {savingName ? 'Saving...' : 'Save name'}
              </button>
            </form>

            <form onSubmit={handleChangePassword} className="space-y-3">
              <h3 className="font-bold text-teal text-sm">Password</h3>
              {[
                ['current', 'Current password', 'current-password'],
                ['next', 'New password', 'new-password'],
                ['confirm', 'Confirm new password', 'new-password'],
              ].map(([key, label, autoComplete]) => (
                <div key={key}>
                  <label className="text-xs uppercase tracking-wide text-label">{label}</label>
                  <input
                    type="password"
                    required
                    autoComplete={autoComplete}
                    value={passwordFields[key]}
                    onChange={(e) => setPasswordFields((prev) => ({ ...prev, [key]: e.target.value }))}
                    className={INPUT_CLASS}
                  />
                </div>
              ))}
              {passwordMessage.text && (
                <p className={`text-sm ${passwordMessage.isError ? 'text-red-600' : 'text-teal'}`}>
                  {passwordMessage.text}
                </p>
              )}
              <button
                type="submit"
                disabled={savingPassword}
                className="bg-mint text-teal rounded-[10px] px-6 py-2.5 font-medium disabled:opacity-50 hover:brightness-90 transition-all duration-200"
              >
                {savingPassword ? 'Saving...' : 'Change password'}
              </button>
            </form>
          </div>

          <div className="mt-6 bg-white border-l-[3px] border-mint rounded-r-lg p-4">
            <h3 className="font-bold text-teal mb-1 text-sm">CV</h3>
            <p className="text-body text-sm">
              {cvS3Key ? `Current CV: ${cvS3Key.split('/').pop()}` : 'No CV uploaded yet.'}
            </p>
            <input
              ref={cvInputRef}
              type="file"
              accept="application/pdf"
              className="hidden"
              onChange={handleCvPick}
            />
            <button
              type="button"
              onClick={() => cvInputRef.current?.click()}
              disabled={cvUploading}
              className="mt-3 border border-card-border text-teal bg-white rounded-[10px] px-4 py-2 text-sm disabled:opacity-50 transition-colors duration-200"
            >
              {cvUploading ? 'Uploading...' : cvS3Key ? 'Replace CV' : 'Upload CV'}
            </button>
            {cvPreview && (
              <p className="text-sm text-teal mt-2">CV updated. Extracted text starts with: "{cvPreview}..."</p>
            )}
            {cvError && <p className="text-sm text-red-600 mt-2">{cvError}</p>}
          </div>
        </section>

        <Divider />

        <section id="active-profile">
          <h2 className="font-bold text-teal mb-4 text-sm uppercase tracking-wide">Active Profile</h2>
          <form onSubmit={handleSaveProfile} className="space-y-4">
            {Object.entries(PROFILE_LABELS).map(([key, label]) => (
              <div key={key}>
                <label className="text-xs uppercase tracking-wide text-label">{label}</label>
                <textarea
                  rows={2}
                  value={fields[key] || ''}
                  onChange={(e) => setFields((prev) => ({ ...prev, [key]: e.target.value }))}
                  className="mt-1 w-full bg-white border border-card-border rounded-[10px] px-4 py-2.5 text-sm text-body focus:outline-none focus:border-mint transition-colors duration-200"
                />
              </div>
            ))}
            {savedMessage && <p className="text-sm text-teal">{savedMessage}</p>}
            <button
              type="submit"
              disabled={savingProfile}
              className="bg-mint text-teal rounded-[10px] px-6 py-2.5 font-medium disabled:opacity-50 hover:brightness-90 transition-all duration-200"
            >
              {savingProfile ? 'Saving...' : 'Save changes'}
            </button>
          </form>
        </section>

        <Divider />

        <section id="your-profiles">
          <h2 className="font-bold text-teal mb-4 text-sm uppercase tracking-wide">Your Profiles</h2>
          <div className="space-y-3">
            {allProfiles.map((p) => (
              <div
                key={p.id}
                className="bg-white border-l-[3px] border-mint rounded-r-lg p-4 flex items-center justify-between gap-3"
              >
                <div>
                  <p className="font-medium text-teal text-sm">
                    {p.label || 'Untitled profile'}
                    {p.is_active && <span className="text-label text-xs ml-2">(active)</span>}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {!p.is_active && (
                    <button
                      type="button"
                      onClick={() => handleSwitch(p.id)}
                      className="border border-card-border text-teal bg-white rounded-[10px] px-3 py-1.5 text-sm transition-colors duration-200"
                    >
                      Switch
                    </button>
                  )}
                  <input
                    type="text"
                    placeholder="New name"
                    value={renameDrafts[p.id] ?? ''}
                    onChange={(e) => setRenameDrafts((prev) => ({ ...prev, [p.id]: e.target.value }))}
                    className="bg-white border border-card-border rounded-[10px] px-2 py-1.5 text-sm w-32"
                  />
                  <button
                    type="button"
                    onClick={() => handleRename(p.id)}
                    className="border border-card-border text-teal bg-white rounded-[10px] px-3 py-1.5 text-sm transition-colors duration-200"
                  >
                    Rename
                  </button>
                </div>
              </div>
            ))}
          </div>
          <button
            type="button"
            onClick={() => navigate('/onboarding')}
            className="mt-4 border border-card-border text-teal bg-white rounded-[10px] px-4 py-2 text-sm transition-colors duration-200"
          >
            + New profile
          </button>
        </section>

        <Divider />

        <section id="history">
          <h2 className="font-bold text-teal mb-4 text-sm uppercase tracking-wide">History</h2>
          {historyError && <PlaceholderNote message={historyError} />}
          {!historyError && !history && <p className="text-body text-sm">Loading history...</p>}
          {!historyError && history && (
            <div className="space-y-2">
              {Object.entries(HISTORY_LABELS).map(([toolKey, label]) => {
                const entries = history[toolKey] || []
                const isOpen = openHistoryTools.has(toolKey)
                const showAll = expandedHistoryTools.has(toolKey)
                const visibleEntries = showAll ? entries : entries.slice(0, HISTORY_PREVIEW_LIMIT)
                const hiddenCount = entries.length - visibleEntries.length
                return (
                  <div key={toolKey} className="border border-card-border rounded-lg overflow-hidden">
                    <button
                      type="button"
                      onClick={() => toggleHistoryTool(toolKey)}
                      className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 text-left transition-colors duration-200"
                    >
                      <span className="font-medium text-teal text-sm">{label}</span>
                      <span className="text-xs text-gray-500">
                        {entries.length} {entries.length === 1 ? 'result' : 'results'} {isOpen ? '▲' : '▼'}
                      </span>
                    </button>
                    {isOpen && (
                      <div className="p-2">
                        {entries.length === 0 ? (
                          <p className="text-body text-sm p-2">No results yet.</p>
                        ) : (
                          <>
                            {visibleEntries.map((entry, i) => {
                              const entryKey = `${toolKey}:${i}`
                              return (
                                <HistoryEntryRow
                                  key={entryKey}
                                  entryKey={entryKey}
                                  entry={entry}
                                  isOpen={openHistoryEntries.has(entryKey)}
                                  onToggle={toggleHistoryEntry}
                                />
                              )
                            })}
                            {hiddenCount > 0 && (
                              <button
                                type="button"
                                onClick={() => toggleShowAllHistory(toolKey)}
                                className="w-full text-center text-xs text-teal py-2 hover:underline"
                              >
                                Show {hiddenCount} older
                              </button>
                            )}
                            {showAll && entries.length > HISTORY_PREVIEW_LIMIT && (
                              <button
                                type="button"
                                onClick={() => toggleShowAllHistory(toolKey)}
                                className="w-full text-center text-xs text-teal py-2 hover:underline"
                              >
                                Show fewer
                              </button>
                            )}
                          </>
                        )}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </section>
      </Card>
    </Layout>
  )
}
