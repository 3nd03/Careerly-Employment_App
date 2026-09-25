import client from './client'

export async function signup({ email, password, display_name }) {
  const { data } = await client.post('/auth/signup', { email, password, display_name })
  return data
}

export async function login({ email, password }) {
  const { data } = await client.post('/auth/login', { email, password })
  return data
}

export async function logout() {
  const { data } = await client.post('/auth/logout')
  return data
}

export async function getMe() {
  const { data } = await client.get('/auth/me')
  return data
}

export async function forgotPassword(email) {
  const { data } = await client.post('/auth/forgot-password', { email })
  return data
}

export async function resetPassword(token, newPassword) {
  const { data } = await client.post('/auth/reset-password', { token, new_password: newPassword })
  return data
}
