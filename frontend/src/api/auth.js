import client from './client'

export async function signup({ email, password, display_name, consent }) {
  const { data } = await client.post('/auth/signup', { email, password, display_name, consent })
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

export async function updateMe(displayName) {
  const { data } = await client.put('/auth/me', { display_name: displayName })
  return data
}

export async function changePassword(currentPassword, newPassword) {
  const { data } = await client.post('/auth/change-password', {
    current_password: currentPassword,
    new_password: newPassword,
  })
  return data
}

export async function deleteAccount() {
  const { data } = await client.delete('/auth/me')
  return data
}
