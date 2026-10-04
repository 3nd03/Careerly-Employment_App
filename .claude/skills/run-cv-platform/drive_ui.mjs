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
import { mkdirSync } from 'node:fs'
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
