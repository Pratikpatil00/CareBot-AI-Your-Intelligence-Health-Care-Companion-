# Verification and how to repeat it

## Verified in the build environment

- **42 pytest tests passed** on Python 3.12 with SQLite.
- Real Tesseract OCR extracted printed text from a generated test image. The complete prescription endpoint then ran with a deterministic Groq HTTP test fixture and forced review of every extracted medicine.
- Real PDFium text extraction read the supplied eight-page synopsis: 14,480 characters.
- DOM integration executed actual page scripts against actual Flask routes, over an isolated test transport: all 15 HTML pages initialized; registration, persistent vitals, medicine creation/dose logging, water logging, profile/BMI, dashboard, chat configuration errors map configuration errors, login measurements, in-app water alerts/snooze, admin login, patient access denial and admin record browsing passed.
- Mappls SDK contract fixtures checked SDK loading, nearby radius/category parameters, coordinates/PIN-based locations, escaped results, details, directions and empty/error responses. These fixtures verify application wiring, not the live Mappls service.
- All frontend JavaScript files passed Node syntax checking. Python sources compiled.
- `frontend/css/style.css` matches the supplied stylesheet byte-for-byte.
- Exactly one runtime `.env` exists, at the root; `.env.example` is a template.

## Not verified live

No Groq or Mappls credentials were supplied. Live AI quality, account quotas, Mappls domain restrictions/API entitlements, map rendering, nearby results and routing still need the local checks in the README. Provider HTTP test fixtures validate requests, schema handling, context, storage and failures; they do not prove live provider behavior.

A Chromium browser launch was blocked by the execution environment's process/socket restrictions. Therefore no full visual browser pass or screenshots are claimed. The included Playwright test is ready to run on your machine. DOM tests use a lightweight Chart constructor stub because they do not test canvas rendering; the delivered app uses real Chart.js.

MySQL, optional medical-model training and clinical accuracy were not tested. No trained weights or fabricated accuracy results are bundled.

## Backend tests

From the root with your Python environment installed:

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q
```

Tests use a disposable SQLite database, temporary uploads, a test-only JWT secret, and provider HTTP fixtures. They do not touch your real records or spend API credits. The real OCR test skips only if Tesseract is not installed.

Coverage includes authentication, HttpOnly/CSRF cookies, persistent logout revocation, restart persistence, record isolation, malformed input, dates/schedules, duplicate doses, timezones, file content/size validation, file cleanup, real OCR, report download/delete ownership, Groq request context, bad AI JSON, provider quotas, missing configuration, emergency escalation static-file protection, admin-only APIs, CLI admin creation, role removal on an active session, patient pagination, login measurement validation, existing complete-project database upgrades, reminder due/snooze/disable/goal/reset behavior and reminder persistence after restart.

## DOM integration test

Install optional Node test dependencies and use your venv Python:

```powershell
npm ci
$env:CAREBOT_TEST_PYTHON = "$PWD\.venv\Scripts\python.exe"
npm run test:dom
```

On Linux/macOS:

```bash
npm ci
CAREBOT_TEST_PYTHON="$PWD/.venv/bin/python" npm run test:dom
```

No running server is required. The test spawns an isolated Flask application through a line-based pipe. It verifies actual DOM event handlers and API payloads; it does not render a browser or call live AI/Maps.

## Mappls SDK contract test

```powershell
npm ci
npm run test:maps
```

This uses SDK boundary fixtures to check our JavaScript integration and error handling. It does not send requests to Mappls or prove that a particular key has access. Complete the README's live Mappls checks with your own domain-restricted Web SDK key.

## Browser smoke test

Run only against a disposable database: the test creates a real test account and records. First install test dependencies:

```powershell
npm ci
npx playwright install chromium
```

In terminal 1, from the root, use a separate test database and leave external keys empty for the explicit configuration-error checks:

```powershell
$env:DATABASE_URL = "sqlite:///$($PWD.Path.Replace('\','/'))/browser-test.db"
$env:PORT = "5010"
$env:GROQ_API_KEY = ""
$env:MAPPLS_API_KEY = ""
.\.venv\Scripts\python.exe run.py
```

In terminal 2:

```powershell
$env:CAREBOT_TEST_URL = "http://localhost:5010"
npm run test:browser
```

Shell variables in these test commands are temporary test-process overrides, not additional `.env` files. `load_dotenv` preserves them. The browser test checks normal forms, reload persistence, error handling, module loading, dashboard and mobile navigation. It writes screenshots into `test-results/`. To test live AI/Maps instead, use the manual README checklist with your real keys; the smoke test intentionally expects missing-key errors.

For an existing compatible Chromium executable, the browser test also accepts `PLAYWRIGHT_EXECUTABLE_PATH`. Browser automation was not executed successfully in the build environment, so inspect the results on your own machine.
