# CareBot AI — integrated project

The supplied HTML/CSS/JavaScript frontend is connected to a Flask backend with persistent SQLAlchemy storage, authenticated accounts, Groq AI, local Tesseract OCR and MapmyIndia / Mappls Web SDK. SQLite works immediately; MySQL is optional. Flask fits the supplied project and supports OCR without adding a separate frontend build system.

**Start with the Windows instructions below. The same server runs both the frontend and backend at `http://localhost:5000`. Do not open HTML files directly or use Live Server.**

## What is implemented

| Feature | Working behavior |
|---|---|
| Accounts | Optional height/weight at registration and login; registration, login, logout, hashed passwords, HttpOnly JWT cookies, CSRF checks, persistent token revocation, isolated patient records |
| Admin panel | Separate admin sign-in, patient search, paginated profile/vitals/medicines/doses/water/documents/chats/analyses, original-file downloads; server-enforced access |
| Dashboard | Saved vitals, seven-day chart, hydration, dose adherence, actual medicine schedules, links to modules |
| Health tracker | Validated readings saved to the database and retained after refresh/restart |
| Health assistant | Groq responses with your recent reports, vitals, medicines and profile; multiple conversations and saved history |
| Reports | PDF/image OCR, DOCX/TXT/CSV extraction, Groq structure/explanation, original text, history, original-file download and deletion |
| Prescription scanner | Image → Tesseract OCR → Groq JSON with names, dosage, frequency, instructions and duration; source text and uncertainties; review before saving medicines |
| Medicine manager | Multiple daily times, date range, edit/delete, taken/missed logs, history, duplicate-dose prevention and open-app reminders |
| Water tracker | Persistent logs and reminder schedule, daily target, timezone, seven-day totals, due banner, 10-minute snooze and optional browser notifications |
| Specialist finder | Groq specialty/urgency explanation, linked to facility search |
| Hospital finder | Mappls map, device location or selected city/address, nearby hospitals/clinics/pharmacies, radius/keyword search, details and directions; ratings/open status shown when supplied |
| Profile/BMI | Age, height, weight, BMI, conditions, allergies, diet preferences and timezone |
| Diet planner | Groq plan based on profile, BMI and the requested goal; saved plans |
| Symptoms | Groq educational possible causes, urgency, next steps and history; optional supervised classifier |
| X-rays | Real image sent to Groq vision for educational observations, saved image/result history; optional locally trained CNN |

No sample patients, fabricated readings, seeded hospitals or canned AI fallbacks are used by the application. Test fixtures exist only in tests.

## Assumptions and important differences from the synopsis

- The ZIP contains an unfinished Flask backend, not only a frontend. This package replaces the incomplete backend and removes the frontend's mock-data paths.
- The original `frontend/css/style.css` is **byte-for-byte unchanged**. The original shell, login structure, existing dashboard layout and design classes are retained. Originally unfinished modules now contain forms in their existing panels. Symptom Checker, Diet Planner and Profile Settings reuse that shell. `features.css` styles new controls only. Authentication/consent text and sample-result text were corrected.
- The supplied login has **Full name + Password**, with no email field. To preserve it, the normalized full name is the unique account name. If two people share a name, use a distinct account name. Registration is an explicit toggle; login does not silently register. Account switching requires authentication; selecting a local name cannot expose another patient's data. There is no email/password-reset service in this scope.
- **Groq replaces Gemini**, as requested. A Groq vision model is not a diagnostic CNN. No trained models or datasets were provided. Therefore the default app does not pretend to have CNN disease predictions or validated disease probabilities. Fully implemented training/inference commands are provided in `docs/MODELS.md`; actual datasets, training and independent evaluation are still required for that part of the synopsis. When a trained local model is installed, its output is passed to Groq and displayed separately, with its limitations.
- Medicine schedules are daily times within a date range. Variable/tapering or “as needed” prescriptions must be reviewed with the prescriber; the scanner never invents schedules. Create separate reviewed schedules if appropriate.
- Reminders work while CareBot is open in the browser. Optional browser notifications require permission. They are **not background push notifications after the browser closes**. Due doses remain visible on reopening; missed doses are not inferred automatically.
- Wearable/smartwatch feeds and live hospital booking are future scope in the synopsis and are not implemented.

## Prerequisites

1. **Python 3.11 or 3.12, 64-bit**. The included dependency lock was tested with Python 3.12. Select “Add python.exe to PATH” on Windows.
2. **Tesseract OCR** with its English language data. `pytesseract` alone is not the OCR executable.
3. An internet connection, a Groq API key and a Mappls Web SDK static key with the required APIs enabled.
4. A current Chrome/Edge/Firefox browser. Location and notifications require localhost or HTTPS.
5. **No separate database installation is needed** for SQLite. For MySQL, see below.
6. **Node.js 22+ is optional**, only for the npm shortcuts and browser tests. The HTML/JS frontend has no npm build step. Chart.js and fonts retain the original CDN-based loading and require internet access.

Tesseract installation:

- Windows: follow the Windows installation guidance linked by the [Tesseract project](https://tesseract-ocr.github.io/tessdoc/Installation.html). A typical binary location is `C:/Program Files/Tesseract-OCR/tesseract.exe`.
- Ubuntu/Debian: `sudo apt install tesseract-ocr tesseract-ocr-eng`
- macOS with Homebrew: `brew install tesseract`

Check it with `tesseract --version`. If it is not on PATH, set `TESSERACT_CMD` in the root `.env` to its full path. PDFs use bundled PDFium through `pypdfium2`; **Poppler is not required**.

## Windows setup — exact commands

1. Extract the ZIP and open the **carebot-ai** folder in VS Code. The root contains `run.py`, `README.md`, `requirements.txt`, `.env` and `.env.example`.
2. Open PowerShell in that folder:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts\init_env.py
```

If Python 3.11 is installed, use `py -3.11` on the first line. Directly invoking `.venv\Scripts\python.exe` avoids PowerShell activation/execution-policy issues.

3. Open the **root `.env`**, add both API keys and configure Tesseract if needed. The setup script generates a random `JWT_SECRET` and preserves existing values. Never paste real keys into `.env.example` or JavaScript.
4. Run the project:

```powershell
.\.venv\Scripts\python.exe run.py
```

5. Open **http://localhost:5000**. Click **New here? Create an account**, enter a distinct full account name and a password of at least eight characters, review the consent, and register.
6. Use **Settings** in the sidebar account menu to save your profile. Restart the server after changing `.env`.

Stop the server with Ctrl+C. Next time, only run the command in step 4; your records remain in `data/carebot.db`.

## Upgrade your existing CareBot installation

1. Stop the old server. Back up your entire project, especially **`.env` and `data/`** (database, uploaded reports and any trained models).
2. Extract this ZIP into a **new folder**. Copy your existing root `.env` and entire `data/` directory into the new `carebot-ai` folder. Do not overwrite your populated `.env` with the blank distributed template. If you use an external `DATABASE_URL`, keep that value and back up that database instead.
3. In the copied `.env`, remove `GOOGLE_MAPS_API_KEY` and add `MAPPLS_API_KEY=your_web_static_key`. Keep your existing `JWT_SECRET`, Groq key, model settings and database URL. Do not copy `.venv`; create/install it using the setup commands above.
4. Run `python scripts/init_env.py`, then create your administrator and start the server. If using the venv without activation, replace `python` with `.\.venv\Scripts\python.exe`.
5. Existing databases from the previously delivered **complete CareBot** package are retained. Startup only adds the new `admin_access` and `water_reminder` tables; no patient is automatically made an admin and no records are deleted. The much older incomplete Phase 2 schema is a different schema and needs a separate migration.
6. Open the new server and hard-refresh the browser (Ctrl+F5) to load updated JavaScript.

## Create your administrator

From the project root, run this once:

```powershell
.\.venv\Scripts\python.exe scripts\create_admin.py
```

Enter a new administrator account name and a password of at least 12 characters. Password input is hidden. There is no default admin password and no public admin registration. Existing patient account names are refused; create a separate admin account.

Start the server and click **Admin sign in** on the login page (or open `/admin-login.html`). Successful admin login opens `/admin.html`. Search patients, select one and choose a record category. Both patient listing and record history have pagination, so older records remain reachable. The admin can read health profiles, vitals, medicines/doses, hydration, uploaded originals/OCR/analysis, chats and saved analyses. Password hashes and authentication tokens are never returned. This is a read-only administration panel; editing/deleting other patients or granting admin roles through the web is not exposed.

The database `AdminAccess` permission is checked on **every admin API request**, not trusted from the browser or a token role claim. Normal patient API routes remain owner-scoped.

## macOS / Linux setup

From the project root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/init_env.py
# Edit the root .env with your own API keys.
.venv/bin/python run.py
```

Open http://localhost:5000. The frontend and API run together. There is no second frontend command or environment file.

Optional npm shortcuts after activating your Python venv:

```bash
npm start
npm test
```

`npm ci` is only necessary for the optional DOM/Mappls-contract/Playwright tests. See `docs/TESTING.md`.

## Get and configure the API keys

### Groq

1. Sign in to [Groq Console](https://console.groq.com/keys).
2. Create an API key and place it in `GROQ_API_KEY` in the root `.env`.
3. Confirm your project has access to the selected text and vision models. Defaults are `openai/gpt-oss-20b` and `qwen/qwen3.8-27b`. Model availability changes; see [supported models](https://console.groq.com/docs/models) and [vision documentation](https://console.groq.com/docs/vision).
4. If needed, change `GROQ_MODEL` and `GROQ_VISION_MODEL` in that same `.env`. Use a text model supporting JSON object mode and a vision model supporting images and JSON mode.
5. Check credentials/model access without sending patient content:

```powershell
.\.venv\Scripts\python.exe scripts\check_services.py
```

The Groq key remains on the backend. Text/profile context is sent to Groq only when an AI feature is requested. X-ray pixels are also sent for vision analysis. Prescription OCR is performed locally, and the extracted text is sent for structuring. Uploaded originals and analysis results are stored locally.

### MapmyIndia / Mappls (replaces Google Maps)

1. Sign in to the [Mappls Console](https://auth.mappls.com/console/) and create/select your Web application.
2. Obtain a **Web SDK static key** from the credentials section. This integration follows the current static-key authentication: the SDK receives the key as `access_token`. It does not use the older OAuth client-ID/client-secret flow.
3. Enable/request access to **Web Maps JS v3, Nearby Search, Place Search / Autosuggest, Place Details / PIN details, and Directions / Routing** for that application. Some access and place fields depend on your plan; confirm the available APIs in your console.
4. Restrict this browser key to your permitted development domains (`localhost`, `127.0.0.1`) and your actual production HTTPS domain, using the domain-whitelisting format accepted by Mappls Console. Use the same hostname consistently when running CareBot.
5. Set `MAPPLS_API_KEY` in the **single root `.env`**, then restart the server. No server-side Mappls secret or OAuth credentials are needed for this Web SDK integration.
6. Open Hospital Finder. Click **Use my location**, or search a city/address and select **Use this location** from the results. Then choose a facility type/radius, search, inspect **Details**, and select **Directions**.

The public Web SDK key is returned by authenticated `/api/maps/config` and is visible in browser requests. Use a domain-restricted Web key, never an unrestricted server secret. Location and place queries go directly to Mappls; patient records and AI histories are not sent to Mappls.

References: [Web Maps JS](https://developer.mappls.com/documentation/sdk/Web/Web%20JS/), [Web plugins](https://github.com/mappls-api/mappls-web-plugins), [Nearby Search](https://developer.mappls.com/documentation/sdk/Web/Mappls%20Web%20Plugins/nearbySearch-plugin/readme/), [Directions](https://developer.mappls.com/documentation/sdk/Web/Mappls%20Web%20Plugins/directions-plugin/readme/).

Ratings and live opening status are displayed only when Mappls supplies them; otherwise the UI says they were not supplied. Do not infer “open” from a missing value. Nearby search uses the chosen radius. A typed keyword overrides the category selector. PIN-based search/directions work when coordinates are not included in your plan. No Google Maps API is loaded or required.

## One root environment file

A `.env` with blank credentials and a placeholder `.env.example` are included. Only **`.env`** is loaded, explicitly from the project root. There are no backend/frontend `.env` files.

```dotenv
GROQ_API_KEY=your_groq_key_here
MAPPLS_API_KEY=your_domain_restricted_web_static_key_here
JWT_SECRET=generated_by_scripts_init_env_py
PORT=5000
DATABASE_URL=
GROQ_MODEL=openai/gpt-oss-20b
GROQ_VISION_MODEL=qwen/qwen3.8-27b
TESSERACT_CMD=C:/Program Files/Tesseract-OCR/tesseract.exe
COOKIE_SECURE=false
```

Leave `DATABASE_URL` empty to use the absolute default `data/carebot.db`. Leave `TESSERACT_CMD` empty when Tesseract is on PATH. `COOKIE_SECURE=false` is for HTTP localhost; use `true` behind HTTPS. Do not copy the illustrative JWT string above: run `init_env.py` to generate a random secret. The distributed `.env` has no credentials.

Optional MySQL:

```sql
CREATE DATABASE carebot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'carebot_app'@'localhost' IDENTIFIED BY 'choose-a-strong-password';
GRANT ALL PRIVILEGES ON carebot.* TO 'carebot_app'@'localhost';
```

Set `DATABASE_URL=mysql+pymysql://carebot_app:URL_ENCODED_PASSWORD@localhost:3306/carebot?charset=utf8mb4` in the same root `.env`. Tables are created on the first startup. A dedicated database is recommended: this schema replaces the incomplete Phase 2 schema and does **not** migrate an old populated database automatically. MySQL was not available for live verification in the build environment.

## Try every major feature

Use non-sensitive test inputs initially.

1. **Login:** register, log out, sign in with height/weight; confirm updated values in Settings/BMI and the tracker. Leave measurements blank on the next login to preserve them. Wrong passwords must not change measurements. A second account must have empty independent records.
2. **Vitals:** log 120 systolic and 74 heart rate. Refresh, restart the server, then inspect the dashboard. The values must remain.
3. **Profile/diet:** save age/height/weight/preferences in Settings, then generate a Diet Planner result. It appears in saved plans.
4. **Chat:** ask “What can you help with?”, then “Explain my last recorded vitals.” Use New Conversation and switch between saved conversations. Quick actions use the saved patient context.
5. **Report analysis:** upload a clear PDF/PNG/JPG or a UTF-8 text report. Check actual extracted fields, source text, uncertainties and explanation. Non-numeric reports also receive a narrative explanation. Download/delete from history.
6. **Prescription OCR:** Medicine Manager → upload a clear printed prescription image → Scan. Compare raw OCR and every structured field against the original. Click **Review in medicine form**, correct any OCR errors, enter prescribed times and dates, then save. Scanning alone never creates a medicine or dose.
7. **Medicines:** create two daily times; log a dose as Taken or Missed. A duplicate for the same medicine/date/time is rejected. Check dashboard adherence. Editing only changes permitted fields.
8. **Reminders:** in Water Tracker, save an interval of **1 minute** and keep a tab open. Saving a nonzero interval enables water reminders immediately; the page shows the next due time. After about a minute (plus up to 15 seconds polling), a water banner appears on any patient page. Snooze delays it by 10 minutes. Logging water resets the interval. Set interval to 0 to disable. **Enable reminders + browser notifications** requests notification permission and uses 60 minutes if reminders were off. **Test reminder** checks immediate alert display. Browser permission is optional for the in-app banner. Due medicines are also checked every 15 seconds when medicine reminders are enabled. Browser throttling or a sleeping device can delay checks; nothing runs after the browser closes.
9. **Water:** log 250 mL, refresh and inspect the dashboard. Day boundaries follow the profile's IANA timezone.
10. **Symptoms/specialist:** describe a concern, read urgency/next steps, and follow “Find nearby care.” Clear emergency phrases are escalated even if Groq is offline. This small rule set is not exhaustive emergency detection.
11. **Maps:** permit location, try each facility type, search by name, change radius, open details/hours, request Directions and inspect the route and steps. Try selecting a city/address result too. An unavailable field must remain unknown.
12. **X-ray:** upload an appropriate image and compare the result with professional interpretation. The default result is labeled Groq vision, never CNN or clinical diagnosis. See `docs/MODELS.md` for the optional trained model path.

13. **Admin:** create an administrator using the command below, sign in through **Admin sign in**, search for a patient, inspect every record type and download an original report. Patient accounts must receive 403 from `/api/admin/patients`; simply visiting `admin.html` must show no records.

## Common errors and fixes

| Problem | Fix |
|---|---|
| `python` / `py` not found | Install Python 3.11/3.12, enable PATH and reopen the terminal. |
| PowerShell blocks activation | Use the explicit `.\.venv\Scripts\python.exe` commands above; activation is not necessary. |
| `ModuleNotFoundError: backend` | Run `python run.py` from the root with `run.py`; do not run `backend/app.py` directly. |
| JWT secret startup error | Run `python scripts/init_env.py`; keep the generated value private. |
| Groq is not configured / key rejected | Set `GROQ_API_KEY` in root `.env`, ensure key/model access, restart. No sample response will substitute for a failed call. |
| Groq 429 / timeout | Wait and retry; check quota and internet. Avoid repeated scans while a request is processing. |
| Groq rejected model/request | Verify model IDs in the Groq console; the vision model must support images and JSON. Update only root `.env`. |
| OCR unavailable | Install the Tesseract executable and English data, then set `TESSERACT_CMD` or PATH. |
| Empty/inaccurate OCR | Use an upright, well-lit, high-resolution scan. Tesseract is unreliable on handwriting; do not infer missing doses. Verify with the prescriber/pharmacist. |
| 413 / upload too large | Limit files to 10 MB, images to 20 megapixels, PDFs to 10 pages. DOCX expansion is bounded. |
| Old `.doc` file | Export to DOCX or PDF. The binary `.doc` format is not supported. |
| Maps blank / authorization error | Set `MAPPLS_API_KEY`, enable Mappls Web SDK + required APIs, verify allowed domains and account quota, restart. Older OAuth credentials are not interchangeable with the Web static key. |
| Directions unavailable | Enable Mappls Directions / Routing for the Web key; ensure the location and destination have a Mappls PIN or coordinates. |
| Water reminder does not appear | Save an interval above 0, keep a patient tab open, check the displayed next due time, and stay below today's target. Read any reminder connection error. Set 1 minute for testing; use Test reminder for immediate display. |
| Admin sign-in rejected | Run `python scripts/create_admin.py` to create a separate admin account. Normal registration always creates a patient. |
| Location/notifications denied | Allow permission in browser site settings; use localhost/HTTPS. City/address search works without location permission. |
| 401 / missing CSRF | Sign in again using the served frontend. Use one hostname consistently; cookies for localhost and 127.0.0.1 are separate. |
| `Secure` cookie on HTTP | For localhost set `COOKIE_SECURE=false`. Use true only with HTTPS. |
| “Account already exists” | Sign in with that exact account name or register a distinct name. Names are case-insensitive. |
| Profile timezone not found | Use an IANA value such as `Asia/Kolkata`; install the included `tzdata` dependency. |
| Charts/fonts missing | Allow the existing Chart.js/Google Fonts CDNs. Saved readings remain accessible in the tracker. |
| Port 5000 in use | Set `PORT=5001` in root `.env`, restart and use the new URL; update Mappls domain restrictions if needed. |
| Old SQLite schema | Back up the old project. Start this package with a new database; an old Phase 2 schema is not compatible. |

## Project structure

```text
carebot-ai/
  .env                     # the only runtime environment file; initially blank keys
  .env.example             # placeholder template
  run.py                   # serves frontend + API with Waitress
  requirements.txt         # tested dependency lock
  requirements-ml.txt      # optional supervised training dependencies
  package.json             # optional npm shortcuts/browser-test dependency
  frontend/
    *.html                 # original pages + synopsis modules/profile
    css/style.css          # original stylesheet unchanged
    css/features.css       # added controls only
    js/                    # authenticated API calls and page behavior
  backend/
    app.py                 # factory, routes, errors, static serving
    config.py              # loads root .env
    extensions.py          # database, JWT, rate limiting
    models.py              # users/profile/vitals/medicines/doses/water/docs/history
    schemas.py             # request and AI response validation
    common.py              # ownership, timezone and response helpers
    routes/                # auth, admin, health, medicines, water, documents, AI, maps
    services/              # Groq, OCR, upload handling and patient context
    ml/                    # optional real training + inference
    tests/                 # isolated integration tests
  scripts/                 # init_env, create_admin, service checks, UI tests
  docs/                    # API, model training, test evidence
  data/                    # generated locally: DB, uploads, optional models
```

## Local use and deployment scope

The server defaults to loopback and is suitable for local academic development. Passwords are hashed, tokens use HttpOnly cookies, writes require CSRF tokens, uploads are private and patient endpoints are owner-scoped. Dedicated admin endpoints check current database permissions before serving patient information. No keys or health request bodies are logged. Uploaded/DB data are **not encrypted at rest by this app**; use OS disk encryption and appropriate access controls.

For a public service, add HTTPS, backups, retention/deletion policy, dependency review, clinical/privacy review, shared rate-limit storage and monitoring. You can set essential deployment options such as `HOST=0.0.0.0` or `RATE_LIMIT_STORAGE_URI=redis://...` in the **same root `.env`**; Redis support needs `pip install redis`. Default rate limits use process memory, appropriate for the single-process local server. Do not expose real patient records from an unreviewed academic deployment. AI results are educational and not clinically validated.
