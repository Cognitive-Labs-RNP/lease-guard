# LeaseGuard AI

LeaseGuard helps commercial tenants and businesses review lease invoices. It extracts relevant lease and invoice terms with RocketRide, validates the AI output before it is trusted, runs deterministic overcharge checks, estimates recovery, and tracks disputes and recovery status.

## Run the demo

Demo Mode is self-contained: it never contacts Supabase, RocketRide, or Gemini and is always marked **DEMO DATA — NOT REAL ANALYSIS**.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Set DEMO_MODE=true in .env
streamlit run app.py
```

On macOS/Linux, activate the environment with `source .venv/bin/activate` and use `cp .env.example .env`.

Open the URL Streamlit prints (normally `http://localhost:8501`). Demo Mode signs in automatically as a local demo user.

## Judge workflow

1. Open **Dashboard** to see the sample portfolio, recovery totals, and risk distribution.
2. Open **Properties** and select each of the three properties.
3. Open **Documents** to inspect the sample lease/invoice extraction results, or upload a `.txt` lease and invoice; Demo Mode uses deterministic sample extraction.
4. Open **Audits**, select a property, review/edit the extracted values, and run the deterministic audit.
5. Open **Findings** to inspect evidence and potential recovery.
6. Open **Recovery** and move a record through Disputed, Under Review, and Recovered.
7. Open **Disputes** to inspect a sample dispute and create/export a reviewable draft.
8. Open **Analytics** to compare multiple properties and review historical risk, findings, and recovery trends.

## Real-service setup

Copy `.env.example` to `.env`, keep `DEMO_MODE=false`, and set these values:

| Variable | Required for | Notes |
| --- | --- | --- |
| `SUPABASE_URL` | sign-in and persistence | Supabase project URL |
| `SUPABASE_KEY` | sign-in and persistence | Supabase anon/public key |
| `ROCKETRIDE_URI` | RocketRide execution | development RocketRide server URI |
| `ROCKETRIDE_APIKEY` | RocketRide execution | development RocketRide API key |
| `ROCKETRIDE_GEMINI_KEY` | Gemini through RocketRide | recommended provider |
| `ROCKETRIDE_GROQ_KEY` + `ROCKETRIDE_GROQ_BASE_URL` | optional fallback | both values are required together |

`SUPABASE_SERVICE_ROLE_KEY` and `ROCKETRIDE_DEPLOY_*` are not used by the Streamlit app; do not put a service-role key in browser/client code.

### Supabase

1. Create a project and enable email/password authentication.
2. In the SQL Editor, run [database/schema.sql](database/schema.sql).
3. Copy the project URL and anon key into `.env`.

The schema creates the app tables and owner-only RLS policies. Sign in before creating or reading real records.

### RocketRide and Gemini

Configure the RocketRide development connection (`ROCKETRIDE_URI`, `ROCKETRIDE_APIKEY`) using `rocketride login` if needed. Add `ROCKETRIDE_GEMINI_KEY` either to `.env` or to RocketRide's server-side environment. The checked-in [lease_extraction.pipe](pipelines/lease_extraction.pipe) is a `chat → llm_gemini → response_answers` pipeline.

The app uses that RocketRide pipeline for:

- lease extraction;
- invoice extraction with invoice-specific JSON requirements; and
- a human-reviewable dispute draft.

No AI result is used for an audit until required values are present and numeric validation passes. Missing, malformed, empty, or incomplete extractions remain reviewable and block the audit rather than producing fabricated findings.

## Real workflow

1. Register, then sign in.
2. Create a property.
3. Upload a readable text PDF or `.txt` lease, then an invoice for that property.
4. Review extraction results on **Documents**; correct incomplete values on **Audits**.
5. Run the audit; saved findings, risk score, recovery record, and evidence appear across the app.
6. Generate and review a RocketRide dispute draft, then track recovery status.
7. Use Dashboard and Analytics to confirm portfolio and multi-property updates.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest tests -v
```

The tests cover RocketRide client integration with mocks, deterministic audit/recovery/risk logic, demo-store behavior, malformed/missing extraction data, and validation failure handling.

## Known limitations

- Live Supabase, RocketRide, and Gemini calls require your own configured accounts and are not exercised by Demo Mode.
- Image uploads are stored but do not include OCR; upload a text-based PDF or `.txt` file for extraction.
- AI-generated dispute text is a draft for human review, not legal advice.
