# Careerly

An AI-powered CV and career platform built for a charity hackathon. Users go through a short onboarding chat and land on a dashboard with tools for skill gap analysis, CV review, cover letters, job role suggestions, LinkedIn outreach, and interview prep.

## Features

- **Accounts**: email/password signup and login, with a 30-day persistent session so returning users don't have to log in every visit.
- **CV-based prefill**: onboarding opens with an optional CV upload. Claude extracts what it can (role, skills, background, experience, tools, location) into an editable review form, so the chatbot only asks what a CV can't answer.
- **Onboarding chatbot**: 11 questions covering target role, skills, background, experience, goals, and any disabilities or access needs. Every other tool uses the profile this builds.
- **Profile page**: inline editing of any profile field, account settings (name, avatar, password), multiple saved profiles per account (e.g. different target roles) with a switcher and rename, and a history view of past results per tool.
- **Dashboard**: profile summary, skill gap score, and links to all tools in one place.
- **Skill gap analysis**: match score against the target role, what the user already has, what they're missing, and concrete next steps.
- **CV analyser**: upload a PDF CV (text extracted with PyPDF2) for a structured review covering overall impression, strengths, weaknesses, and specific rewrite suggestions.
- **Cover letter generator**: takes the user profile and a pasted job description and produces a tailored cover letter.
- **Job role suggestions**: three roles to go for now, three to aim for in six months.
- **LinkedIn message generator**: short cold outreach message built from the user profile, with an optional context field for who they're messaging.
- **Interview prep**: five role-specific questions weighted towards the user's known skill gaps.
- **Career roadmap**: a plan from where the user is now through three months, six months, and one year out.
- **Salary insights**: expected pay range by seniority level, the factors that move it, and negotiation tips.
- **CV download**: rewrite an uploaded or pasted CV and download it as a formatted PDF.
- **CV translator**: translate an uploaded or pasted CV into another language and download it as a PDF.
- **Application tracker**: log job applications with company, role, and status (Applied, Interview, Offer, Rejected), and update status as it changes.
- **Follow-up chat**: after using any tool, the user can ask a specific question about their result and get an answer grounded in that result and their profile.

## Setup

Requires Python 3.10+ and an Anthropic API key.

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

`pip install -e .` is required on every machine. It makes the absolute imports (`from app...`, `from services...`) work correctly.

Copy `.env.example` to `.env` and fill in your own values:

```
ANTHROPIC_API_KEY=your_key_here
S3_BUCKET_NAME=your_bucket_name
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=your_region
DATABASE_URL=postgresql://user:password@host:5432/dbname
FRONTEND_URL=http://localhost:3000
```

## Running the app

```bash
streamlit run app/main.py
```

## Running the API

A FastAPI backend exposing the same tools over HTTP lives in `api/`, used by the React frontend below.

```bash
uvicorn api.main:app --reload
```

## Running the frontend

A React frontend (Vite + Tailwind) lives in `frontend/` and talks to the FastAPI backend above.

```bash
cd frontend
npm install
npm run dev
```

Opens at `http://localhost:3000`.

### Testing on a phone (same WiFi)

Both servers need to be reachable on the LAN, not just `localhost`:

```bash
uvicorn api.main:app --reload --host 0.0.0.0
```

```bash
cd frontend
npm run dev -- --host
```

Find this machine's LAN IP (`ipconfig` on Windows, look for IPv4 Address) and open `http://<LAN-IP>:3000` on the phone. The frontend's API base URL already follows whatever host it was loaded from, so this works without extra config.

## Running tests

```bash
pip install pytest
pytest
```

Tests mock the Anthropic, database, and bcrypt calls, so they run without a real API key, database, or AWS credentials. `scripts/check_db_connection.py` and `scripts/check_s3_connection.py` are separate, manual scripts that hit the real database and S3 bucket to confirm your `.env` credentials work; they are not part of the automated test suite.

## Project structure

```
app/
  main.py              Entry point, routing via st.session_state.page, login gate
  auth.py              Signup, login, logout, remember-me cookie handling
  profile.py           Account settings, profile editing/switching, history
  chatbot.py           Onboarding flow, CV-based prefill
  dashboard.py         Profile summary, skill gap score, tool links
  skill_gap.py         Skill gap analysis
  cv_analyser.py       CV scoring and rewrite suggestions
  cover_letter.py      Cover letter generator
  job_roles.py         Job role suggestions
  linkedin_message.py  LinkedIn outreach message
  interview_prep.py    Interview question prep
  career_roadmap.py    Career roadmap (now / 3mo / 6mo / 1yr)
  salary_insights.py   Salary range and negotiation tips
  cv_download.py       CV rewrite and PDF download
  cv_translator.py     CV translation and PDF download
  application_tracker.py  Job application log with status tracking

services/
  claude_client.py     Single call_claude(prompt, system=""): all API calls go here
  s3_client.py         AWS S3 storage, handles CV PDFs and avatar uploads
  auth_service.py      Password hashing/verification (bcrypt)

database/
  db_client.py         RDS Postgres: users, profiles, and per-tool result history

prompts/
  skill_gap_prompt.py
  cv_prompt.py
  cover_letter_prompt.py
  job_roles_prompt.py
  linkedin_prompt.py
  interview_prep_prompt.py
  profile_extraction_prompt.py
  career_roadmap_prompt.py
  salary_insights_prompt.py
  cv_download_prompt.py
  cv_translator_prompt.py

utils/
  helpers.py           Shared profile rendering and navigation helpers
  pdf.py               PDF text extraction, shared by CV Analyser and onboarding prefill

api/
  main.py              FastAPI app
  routers/             One router per feature area (profile, tools, auth, ...)

frontend/
  src/pages/           One page per route (dashboard, profile, each tool)
  src/components/      Shared UI (Layout, Card, BottomNav, Logo, ...)
  src/api/             Axios client and API calls

tests/                 Automated pytest suite (mocked, no real credentials needed)

scripts/               Manual scripts that hit real infrastructure (DB, S3) to verify .env credentials
```

## Architecture

- All API calls go through `services/claude_client.py`. Nothing else touches the API directly.
- `call_claude` initialises the client inside the function on every call rather than at module level, so a rotated API key is always picked up without restarting the app.
- Absolute imports work throughout via the editable install in `pyproject.toml`. No `sys.path` workarounds.
- Page state and tool results are cached in `st.session_state`. Switching pages never triggers a repeat API call.
- Each feature saves its result to its own table in RDS, linked by `profile_id` rather than a browser session. Results are append-only, so past runs stay visible in the profile page's history rather than being overwritten by the next run.
- CV uploads go to S3, and the returned key gets stored alongside the profile.
- If a save to S3 or RDS fails, the app shows a warning and carries on. A database issue never blocks the user from finishing their session.

## Data persistence

- Uploaded CV PDFs and avatars are stored in S3.
- Everything else (accounts, profiles, and every tool's results) is stored in RDS Postgres. A user can hold multiple profiles (e.g. different target roles); one is marked active at a time, and every result table keys off `profile_id`.
- Login is by account (email/password), not a browser session. A signed, server-validated token in a cookie keeps a user logged in for 30 days without re-entering credentials.

## Accessibility, security and cost

**Accessibility**

Runs in the browser with no install required, works with whatever device someone brings on the day. Outputs from Claude are written in plain language rather than technical jargon. Standard keyboard navigation works out of the box through Streamlit's default components. Onboarding now asks directly about disabilities or access needs, so the profile can account for this going forward. Screen reader and font scaling testing hasn't been done yet, that's a clear next step if this goes further.

**Security**

API keys and AWS credentials live in `.env`, which is never committed. The AWS IAM user is scoped to only the S3 and RDS access it needs. Passwords are hashed with bcrypt, never stored in plain text. The persistent login cookie holds an opaque, randomly generated token that's checked against the database on every use, not the user's credentials themselves, and is invalidated server-side on logout. RDS only accepts connections from specific whitelisted IP addresses.

**Cost**

The Claude API is pay-per-token, so cost tracks usage rather than sitting at a fixed monthly rate. AWS is on the free tier for this prototype. A production version serving real users would need proper hosting and would scale in cost with the number of users, worth scoping properly with the charity rather than estimating here.

## Known limitations

- Built in a single day. This is a working prototype, not a production system.
- No consent flow, data retention policy, or way for a user to request their data be deleted. Needed before any real deployment, since CVs contain personal data.
- No password reset flow. A user who forgets their password currently has no way to recover the account.
- Built with one user in mind at a time, not tested under concurrent load.

## Roadmap

Features we'd want to add if this moves beyond the prototype stage:

- **Text to speech**: read questions and results aloud, for users who find reading difficult or have visual impairments.
- **Microphone (speech to text)**: answer onboarding questions by voice instead of typing.
- **Job postings**: pull in live roles matched to the user's profile, rather than just suggesting role types.
- **Culture alignment**: help users understand whether a company's culture is a good fit, not just whether their skills match.
- **Career path videos**: short videos showing what a real career path looks like for a given role, to make the suggestions feel less abstract.
