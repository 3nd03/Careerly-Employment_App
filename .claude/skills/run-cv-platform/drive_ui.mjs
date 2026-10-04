// Drive the Careerly frontend in headless Chrome and screenshot each step.
//
//   node .claude/skills/run-cv-platform/drive_ui.mjs <email> <password> [page ...]
//
// With just credentials it runs the default flow: signup invalid-email error, login, then
// application tracker add -> change status -> delete (reloading to confirm each change saved).
// Extra args are page paths without the leading slash (e.g. dashboard profile) to log in and
// screenshot instead - Git Bash rewrites "/dashboard" into a Windows path.
// The account must already exist with a profile - smoke.py --ui creates one and cleans it up.
// Screenshots: .claude/skills/run-cv-platform/out/*.png
import { createRequire } from 'node:module'
import { mkdirSync, readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const here = path.dirname(fileURLToPath(import.meta.url))
const out = path.join(here, 'out')
mkdirSync(out, { recursive: true })
const { chromium } = createRequire(path.join(here, '.deps', 'node_modules', 'x.js'))('playwright-core')

const WEB = 'http://localhost:5173'
const [email, password, ...pageArgs] = process.argv.slice(2)
const paths = pageArgs.map((p) => '/' + p.replace(/^\/+/, ''))
if (!email || !password) {
  console.error('usage: node drive_ui.mjs <email> <password> [page ...]')
  process.exit(2)
}

const browser = await chromium.launch({ channel: 'chrome', headless: true })
const page = await browser.newPage({ viewport: { width: 1200, height: 900 } })
const errors = []
page.on('pageerror', (e) => errors.push(e.message))
page.on('console', (m) => {
  // The 422 from the deliberate invalid-email signup is logged by the browser; ignore it.
  if (m.type() === 'error' && !m.text().includes('422')) errors.push(m.text())
})
const shot = async (name) => {
  const file = path.join(out, `${name}.png`)
  await page.screenshot({ path: file })
  console.log(`  screenshot ${file}`)
}
const step = (msg) => console.log(`- ${msg}`)

try {
  if (paths.length === 0) {
    step('signup with invalid email shows friendly error')
    await page.goto(`${WEB}/signup`)
    await page.fill('input[type="email"]', 'a@b')
    const pw = page.locator('input[type="password"]')
    await pw.nth(0).fill('password123')
    await pw.nth(1).fill('password123')
    await page.click('button[type="submit"]')
    await page.waitForSelector('text=Please enter a valid email address.', { timeout: 10000 })
    await shot('signup-invalid-email')
  }

  step(`log in as ${email}`)
  await page.goto(`${WEB}/login`)
  await page.fill('input[type="email"]', email)
  await page.fill('input[type="password"]', password)
  await page.click('button[type="submit"]')
  await page.waitForURL((u) => !u.pathname.startsWith('/login'), { timeout: 15000 })
  step(`landed on ${new URL(page.url()).pathname}`)

  if (paths.length > 0) {
    for (const p of paths) {
      await page.goto(`${WEB}${p}`)
      await page.waitForLoadState('networkidle')
      await shot(p.replace(/\W+/g, '-').replace(/^-|-$/g, '') || 'root')
    }
  } else {
    step('application tracker: add')
    await page.goto(`${WEB}/application-tracker`)
    await page.waitForSelector('text=Add an application')
    const form = page.locator('form')
    await form.locator('input[type="text"]').nth(0).fill('Smoke Test Ltd')
    await form.locator('input[type="text"]').nth(1).fill('QA Engineer')
    await form.locator('input[type="date"]').fill('2026-10-04')
    await page.click('button:has-text("Add application")')
    const row = () => page.locator('tr', { hasText: 'Smoke Test Ltd' })
    await row().waitFor()

    step('application tracker: change status to Offer, reload')
    const put = page.waitForResponse((r) => r.request().method() === 'PUT' && r.url().includes('/tools/applications/'))
    await row().locator('select').selectOption('Offer')
    if ((await put).status() !== 200) throw new Error(`status update returned ${(await put).status()}`)
    await page.reload()
    await row().waitFor()
    const status = await row().locator('select').inputValue()
    if (status !== 'Offer') throw new Error(`status after reload is ${status}, expected Offer`)
    await shot('tracker-status-offer')

    step('application tracker: delete, reload')
    const del = page.waitForResponse((r) => r.request().method() === 'DELETE')
    await row().locator('button:has-text("Delete")').click()
    if ((await del).status() !== 200) throw new Error(`delete returned ${(await del).status()}`)
    await page.reload()
    await page.waitForLoadState('networkidle')
    if ((await row().count()) !== 0) throw new Error('row still present after delete + reload')
    await shot('tracker-deleted')

    step('profile: rename updates the sidebar')
    await page.goto(`${WEB}/profile`)
    await page.waitForSelector('text=Display name')
    const nameInput = page.locator('form', { hasText: 'Display name' }).locator('input')
    await nameInput.fill('Renamed Smoke')
    await page.click('button:has-text("Save name")')
    await page.waitForSelector('text=Name updated.')
    await page.reload()
    await page.waitForSelector('text=Display name')
    if ((await nameInput.inputValue()) !== 'Renamed Smoke') throw new Error('name did not persist after reload')
    if ((await page.locator('aside, nav').filter({ hasText: 'Renamed Smoke' }).count()) === 0) {
      throw new Error('sidebar does not show the new name')
    }

    step('profile: wrong current password is rejected, correct one changes it')
    const pwForm = page.locator('form', { hasText: 'Current password' })
    const pwInputs = pwForm.locator('input[type="password"]')
    await pwInputs.nth(0).fill('wrong-password')
    await pwInputs.nth(1).fill('newpassword456')
    await pwInputs.nth(2).fill('newpassword456')
    await page.click('button:has-text("Change password")')
    await page.waitForSelector('text=Current password is incorrect')
    // The browser logs the deliberate 400 as a console error; drop just that one.
    const expected = errors.findIndex((e) => e.includes('400'))
    if (expected !== -1) errors.splice(expected, 1)
    await pwInputs.nth(0).fill(password)
    await page.click('button:has-text("Change password")')
    await page.waitForSelector('text=Password changed.')
    await shot('profile-account')

    step('forgot password: generic message, emailed link resets the password')
    const context = await browser.newContext()
    const anon = await context.newPage()
    await anon.goto(`${WEB}/forgot-password`)
    await anon.fill('input[type="email"]', email)
    await anon.click('button[type="submit"]')
    await anon.waitForSelector("text=we've sent a link to reset your password")
    await anon.screenshot({ path: path.join(out, 'forgot-password.png') })
    // start.sh runs the API with EMAIL_BACKEND=console, so the email (with the link) lands in api.log.
    const escapedEmail = email.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const linkPattern = new RegExp(String.raw`to=${escapedEmail}[\s\S]*?(http://\S+/reset-password\?token=[\w-]+)`)
    let link
    for (let i = 0; i < 20 && !link; i++) {
      link = readFileSync(path.join(out, 'api.log'), 'utf8').match(linkPattern)?.[1]
      if (!link) await anon.waitForTimeout(250)
    }
    if (!link) throw new Error('no reset link for this user in out/api.log (is the API running with EMAIL_BACKEND=console?)')
    await anon.goto(link)
    const resetInputs = anon.locator('input[type="password"]')
    await resetInputs.nth(0).fill('resetpassword789')
    await resetInputs.nth(1).fill('resetpassword789')
    await anon.click('button:has-text("Reset password")')
    await anon.waitForURL('**/login')
    await anon.fill('input[type="email"]', email)
    await anon.fill('input[type="password"]', 'resetpassword789')
    await anon.click('button[type="submit"]')
    await anon.waitForURL((u) => !u.pathname.startsWith('/login'), { timeout: 15000 })
    step('logged in with the reset password')
    await context.close()
  }

  if (errors.length) throw new Error(`browser errors: ${errors.join(' | ')}`)
  console.log('UI OK')
} catch (e) {
  await shot('failure').catch(() => {})
  console.error(`UI FAILED: ${e.message}`)
  process.exitCode = 1
} finally {
  await browser.close()
}
