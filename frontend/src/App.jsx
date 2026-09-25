import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'

import { getMe } from './api/auth'
import Login from './pages/Login'
import Signup from './pages/Signup'
import ForgotPassword from './pages/ForgotPassword'
import ResetPassword from './pages/ResetPassword'
import Onboarding from './pages/Onboarding'
import Dashboard from './pages/Dashboard'
import Profile from './pages/Profile'
import SkillGap from './pages/SkillGap'
import CvAnalyser from './pages/CvAnalyser'
import CoverLetter from './pages/CoverLetter'
import JobRoles from './pages/JobRoles'
import LinkedInMessage from './pages/LinkedInMessage'
import InterviewPrep from './pages/InterviewPrep'
import CvDownload from './pages/CvDownload'
import CareerRoadmap from './pages/CareerRoadmap'
import SalaryInsights from './pages/SalaryInsights'
import ApplicationTracker from './pages/ApplicationTracker'
import CvTranslator from './pages/CvTranslator'
import TailoredCvBuilder from './pages/TailoredCvBuilder'

function ProtectedRoute({ children }) {
  const token = localStorage.getItem('token')
  if (!token) {
    return <Navigate to="/login" replace />
  }
  return children
}

export default function App() {
  useEffect(() => {
    if (!localStorage.getItem('token')) return
    getMe()
      .then((user) => {
        localStorage.setItem('email', user.email)
        if (user.display_name) {
          localStorage.setItem('display_name', user.display_name)
        } else {
          localStorage.removeItem('display_name')
        }
        if (user.avatar_s3_key) {
          localStorage.setItem('avatar_s3_key', user.avatar_s3_key)
        } else {
          localStorage.removeItem('avatar_s3_key')
        }
      })
      .catch(() => {})
  }, [])

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />

        <Route
          path="/onboarding"
          element={
            <ProtectedRoute>
              <Onboarding />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          }
        />
        <Route
          path="/skill-gap"
          element={
            <ProtectedRoute>
              <SkillGap />
            </ProtectedRoute>
          }
        />
        <Route
          path="/cv-analyser"
          element={
            <ProtectedRoute>
              <CvAnalyser />
            </ProtectedRoute>
          }
        />
        <Route
          path="/cover-letter"
          element={
            <ProtectedRoute>
              <CoverLetter />
            </ProtectedRoute>
          }
        />
        <Route
          path="/job-roles"
          element={
            <ProtectedRoute>
              <JobRoles />
            </ProtectedRoute>
          }
        />
        <Route
          path="/linkedin-message"
          element={
            <ProtectedRoute>
              <LinkedInMessage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/interview-prep"
          element={
            <ProtectedRoute>
              <InterviewPrep />
            </ProtectedRoute>
          }
        />
        <Route
          path="/cv-download"
          element={
            <ProtectedRoute>
              <CvDownload />
            </ProtectedRoute>
          }
        />
        <Route
          path="/career-roadmap"
          element={
            <ProtectedRoute>
              <CareerRoadmap />
            </ProtectedRoute>
          }
        />
        <Route
          path="/salary-insights"
          element={
            <ProtectedRoute>
              <SalaryInsights />
            </ProtectedRoute>
          }
        />
        <Route
          path="/application-tracker"
          element={
            <ProtectedRoute>
              <ApplicationTracker />
            </ProtectedRoute>
          }
        />
        <Route
          path="/cv-translator"
          element={
            <ProtectedRoute>
              <CvTranslator />
            </ProtectedRoute>
          }
        />
        <Route
          path="/tailored-cv-builder"
          element={
            <ProtectedRoute>
              <TailoredCvBuilder />
            </ProtectedRoute>
          }
        />

        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
