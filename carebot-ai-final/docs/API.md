# API reference

Base URL: `http://localhost:5000/api`. Success: `{ "success": true, "data": ... }`. Errors: `{ "success": false, "message": "..." }` with a meaningful HTTP status. Requests are JSON except file uploads. Unknown fields are rejected on validated write requests.

Authentication uses HttpOnly `access_token_cookie`. Registration/login also set the readable `csrf_access_token` cookie. For POST/PUT/DELETE after login, include its value in `X-CSRF-TOKEN`. The frontend does this in `js/api.js`. Credentials do not go into localStorage. All data endpoints require a valid session unless marked public.

## Routes

| Method | Route | Purpose / request |
|---|---|---|
| GET | `/healthz` | Public health check; reports whether Groq is configured, not its secret |
| POST | `/auth/register` | Public: `{name,password,consent:true,height_cm?:number,weight_kg?:number}`; creates account/session |
| POST | `/auth/login` | Public: same shape; verifies existing account |
| POST | `/auth/admin-login` | Public login, same credentials; requires database admin permission |
| GET | `/auth/me` | Current account |
| POST | `/auth/logout` | Revokes current token persistently and removes cookies |
| GET, PUT | `/profile` | Current health profile; PUT replaces validated profile settings |
| GET, POST | `/health/measurements` | Read / append readings; POST fields: bp_systolic, bp_diastolic, heart_rate, weight_kg, height_cm (optional individually) |
| DELETE | `/health/measurements/:id` | Delete own reading |
| GET | `/dashboard` | Latest readings, BMI, last seven days, water, doses, adherence, source counts |
| GET, POST | `/medicines` | List / create daily medicine schedule |
| PUT, DELETE | `/medicines/:id` | Replace schedule / delete medicine and its logs |
| GET | `/medicines/schedule` | Today's scheduled doses in profile timezone; taken/missed/due/upcoming |
| POST | `/medicines/:id/log` | `{scheduled_date:"YYYY-MM-DD",scheduled_time:"HH:mm",status:"taken" or "missed"}` |
| GET | `/medicines/:id/logs` | Dose history |
| POST | `/water/log` | `{amount_ml:250}` |
| GET | `/water/logs` | Recent water logs |
| DELETE | `/water/logs/:id` | Delete own water log |
| GET | `/water/summary` | Daily/weekly totals and target |
| GET | `/water/reminder` | Persistent schedule: enabled, due, next_due_at, interval_minutes, goal_met |
| POST | `/water/reminder/snooze` | Snooze current user's enabled water reminder for 10 minutes |
| POST | `/reports/upload` | Multipart field `file`; PDF/PNG/JPG/WEBP/DOCX/TXT/CSV |
| POST | `/prescriptions/scan` | Multipart `file`; PNG/JPG/WEBP; OCR then Groq structure |
| POST | `/xray/analyze` | Multipart `file` and `region` (`chest` or `bone`) |
| GET | `/documents?kind=report` | Document history; optional kind: report/prescription/xray |
| GET | `/documents/:id` | Full saved result, source text, OCR metadata |
| GET | `/documents/:id/file` | Private original-file download |
| DELETE | `/documents/:id` | Delete record and original file |
| POST | `/assistant/chat` | `{message,thread_id:"UUID"}`; actual provider response with saved context |
| GET | `/assistant/history?thread_id=UUID` | Current user's exchanges; most recent first |
| GET | `/assistant/threads` | Conversation picker entries |
| POST | `/symptoms/analyze` | `{symptoms:"..."}` |
| POST | `/specialists/recommend` | `{symptoms:"..."}` |
| POST | `/diet/plan` | `{goal:"..."}`; requires saved age/weight/height |
| GET | `/analyses` | Saved symptom/diet/specialty results |
| GET | `/maps/config` | Public domain-restricted Mappls Web SDK key and provider name |

List endpoints with limits accept `?limit=50`, capped at 200. Patient health endpoints are filtered by authenticated user ID; the client cannot choose a user ID. Admin endpoints below separately authorize cross-patient reads. Map search/directions requests go from the browser to Mappls Web SDK/plugins. No fabricated server facility list is used.

Medicine request example:

```json
{
  "name": "Name on prescription",
  "dosage": "Dose exactly as prescribed",
  "instructions": "Instructions exactly as prescribed",
  "schedule_times": ["08:30", "20:30"],
  "start_date": "2026-10-15",
  "end_date": null,
  "reminder_enabled": true
}
```

Profile fields: age, gender, weight_kg, height_cm, known_conditions, preferences, allergies, water_target_ml, water_reminder_minutes, timezone. GET also returns computed `bmi`; omit that computed field on PUT.

## Failure behavior

- 401: absent/expired/revoked session or invalid CSRF.
- 404: missing or another user's record (does not reveal existence).
- 409: duplicate account or already-logged scheduled dose.
- 413: file exceeds 10 MB.
- 415: unsupported file extension.
- 422: invalid input, corrupted/unreadable file, empty OCR or excessive pages/content.
- 429: local rate limit or Groq quota/rate limit.
- 502/503/504: provider/schema failure, missing configuration/dependency or timeout.

Unsuccessful OCR/AI uploads remove temporary stored files and do not create fake successful results. Text and structured AI results are escaped in the frontend, not injected as HTML. AI output JSON is schema-validated; malformed output gets one retry and then fails explicitly.

## Administrator endpoints

All routes below require a valid JWT session **and** a current `AdminAccess` database row. Missing role returns 403. Public registration rejects extra role fields. Password hashes, token data and internal file storage paths are excluded.

| Method | Route | Result |
|---|---|---|
| GET | `/admin/patients?q=NAME&page=1` | Non-admin accounts, name filter, 50 per page |
| GET | `/admin/patients/:id` | Account, full health profile, record counts |
| GET | `/admin/patients/:id/records/:kind?page=1` | All history paginated by 50; `measurements`, `medicines`, `doses`, `water`, `documents`, `chats`, `analyses` |
| GET | `/admin/patients/:id/documents/:document_id/file` | Authorized original download, document must belong to selected patient |

Paginated responses: `{items,page,total,has_more}`. No patient/admin browser endpoint grants administrative access. Use the local `scripts/create_admin.py` command.

Login height/weight are optional and validated. Omitted/null values keep the old value; supplied login values update the profile and append a measurement only after successful authentication. Water settings remain in `/profile`; changing interval/target/timezone restarts the schedule. Logging/deleting water resets the interval. Reaching the target pauses reminders to the next local day. The client polls every 15 seconds while open; it does not implement closed-browser push.
