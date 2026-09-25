import client from './client'

export async function runSkillGap() {
  const { data } = await client.post('/tools/skill-gap')
  return data
}

export async function runCvAnalyse(file) {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await client.post('/tools/cv-analyse', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function runCoverLetter(jobDescription) {
  const { data } = await client.post('/tools/cover-letter', { job_description: jobDescription })
  return data
}

export async function runJobRoles() {
  const { data } = await client.post('/tools/job-roles')
  return data
}

export async function runLinkedInMessage(context) {
  const { data } = await client.post('/tools/linkedin-message', { context })
  return data
}

export async function runInterviewPrep() {
  const { data } = await client.post('/tools/interview-prep')
  return data
}

export async function runTailoredCv(jobDescription, cvText) {
  const { data } = await client.post('/tools/tailored-cv', {
    job_description: jobDescription,
    cv_text: cvText,
  })
  return data
}

export async function runCvDownload(cvText) {
  const { data } = await client.post(
    '/tools/cv-download',
    { cv_text: cvText },
    { responseType: 'blob' }
  )
  return data
}

export async function runCareerRoadmap() {
  const { data } = await client.post('/tools/career-roadmap')
  return data
}

export async function runSalaryInsights() {
  const { data } = await client.post('/tools/salary-insights')
  return data
}

export async function runCvTranslate(cvText, targetLanguage) {
  const { data } = await client.post(
    '/tools/cv-translate',
    { cv_text: cvText, target_language: targetLanguage },
    { responseType: 'blob' }
  )
  return data
}

export async function getApplications() {
  const { data } = await client.get('/tools/applications')
  return data
}

export async function addApplication({ company, role, date_applied, status }) {
  const { data } = await client.post('/tools/applications', { company, role, date_applied, status })
  return data
}

export async function updateApplicationStatus(applicationId, status) {
  const { data } = await client.put(`/tools/applications/${applicationId}`, { status })
  return data
}

export async function runFollowup(toolName, previousResult, question) {
  const { data } = await client.post('/tools/followup', {
    tool_name: toolName,
    previous_result: previousResult,
    question,
  })
  return data
}

export function downloadBlob(blob, filename) {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}
