# LeaseGuard AI - Phase 6: Complete Integration & Hackathon Readiness

> **v1.0.0** — Enterprise Lease Audit Platform with AI-Driven Risk Analysis & Revenue Recovery

## 📋 Overview

LeaseGuard AI is a comprehensive lease audit platform that combines deterministic business rules with AI-powered document extraction. It helps commercial property managers identify lease compliance issues, calculate potential recovery amounts, and track recovery status.

**Phase 6** focuses on production-ready integration, error handling, validation, and demo mode for easy demonstration without external dependencies.

---

## 🚀 Quick Start (5 minutes with Demo Mode)

```bash
# 1. Clone/extract the project
cd lease-guard

# 2. Create Python environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate     # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Enable demo mode
cp .env.example .env
echo "DEMO_MODE=true" >> .env

# 5. Run Streamlit
streamlit run app.py
```

Open http://localhost:8501 in your browser. You're ready to demo!

---

## 📦 Installation & Setup

### 1. Environment Setup

```bash
# Clone the repository
git clone <repo-url>
cd lease-guard

# Create Python virtual environment
python -m venv .venv

# Activate environment
# Windows:
.\.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration (.env file)

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# ============================================================================
# Supabase Configuration (Required)
# ============================================================================
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key  # Optional, for admin ops

# ============================================================================
# AI Provider Configuration (Choose at least ONE)
# ============================================================================

# Option 1: Google Gemini (Recommended)
ROCKETRIDE_GEMINI_KEY=your-gemini-api-key

# Option 2: Groq (Fallback)
ROCKETRIDE_GROQ_KEY=your-groq-api-key
ROCKETRIDE_GROQ_BASE_URL=https://api.groq.com/openai/v1

# ============================================================================
# Demo Mode (Optional)
# ============================================================================
DEMO_MODE=false  # Set to "true" to use sample data
```

### 3. Supabase Database Setup

#### 3a. Create Supabase Project

1. Go to https://supabase.com
2. Click "New Project"
3. Choose organization, project name, password, region
4. Wait for provisioning (2-3 minutes)
5. Copy the project URL and API keys to `.env`

#### 3b. Load Database Schema

1. In Supabase Dashboard, click **SQL Editor**
2. Click **New Query**
3. Copy contents of `database/schema.sql`
4. Paste into editor and click **Run**

This creates all required tables:
- `auth.users` (managed by Supabase Auth)
- `properties`
- `documents`
- `audits`
- `findings`
- `risk_scores`
- `recovery_records`
- `disputes`

### 4. AI Provider Setup

**Choose ONE provider:**

#### Option A: Google Gemini (Recommended)

1. Go to https://ai.google.dev/
2. Click "Get API Key"
3. Create a new API key
4. Copy to `.env`:
   ```env
   ROCKETRIDE_GEMINI_KEY=sk-xxx...
   ```

#### Option B: Groq (Fallback/Free)

1. Go to https://console.groq.com
2. Sign up/login
3. Create an API key
4. Copy to `.env`:
   ```env
   ROCKETRIDE_GROQ_KEY=gsk_xxx...
   ROCKETRIDE_GROQ_BASE_URL=https://api.groq.com/openai/v1
   ```

### 5. Run the Application

```bash
streamlit run app.py
```

The app will start at http://localhost:8501

---

## 🎭 Demo Mode

Demo Mode allows you to:
- Demonstrate the entire product without RocketRide/Gemini/Supabase
- Create realistic sample data automatically
- Test all workflows
- Practice presentations

### Enable Demo Mode

Edit `.env`:

```env
DEMO_MODE=true
```

When enabled:
- ✓ Sample properties are auto-loaded
- ✓ Sample lease/invoice data uses local extraction
- ✓ All findings, risk scores, and recovery records are pre-populated
- ✓ Dashboard shows realistic KPIs
- ✓ All pages show "🎭 DEMO MODE" banner

### Demo Mode Data

Demo includes:
- **3 sample properties** (Office, Retail, Industrial)
- **12 sample findings** (various categories and severities)
- **3 audits** (one per property)
- **10 recovery records** (different statuses)
- **6 sample disputes** (Draft to Recovered)

All data is clearly labeled as `[DEMO]` for transparency.

---

## 🔄 Complete End-to-End Workflow

### Scenario: Audit a Commercial Lease

#### Step 1: Sign In
1. Click "Register" tab
2. Enter email and password
3. Click "Register"
4. Sign in with same credentials

#### Step 2: Create Property
1. Click "Properties" page
2. Click "Add Property" tab
3. Fill in property details:
   - Name: "My Office Building"
   - Address, City, State, ZIP
   - Type: "Office"
4. Click "Create Property"

#### Step 3: Upload Lease Document
1. Click "Documents" page
2. Click "Upload Document" tab
3. Select property "My Office Building"
4. Document Type: "Lease"
5. Upload a lease PDF (or use sample PDF)
   - Extraction runs automatically
   - Extracted data shown in "View Documents"
6. If extraction fails, manual entry will work

#### Step 4: Upload Invoice Document
1. In "Upload Document" tab
2. Select same property
3. Document Type: "Invoice"
4. Upload invoice PDF
   - Extraction runs automatically

#### Step 5: Run Audit
1. Click "Audits" page
2. Click "Run Audit" tab
3. Select property "My Office Building"
4. Lease data auto-fills from extracted document
5. Invoice data auto-fills from extracted document
6. Click "Run Deterministic Audit"
   - Findings are generated (CAM cap violations, etc.)
   - Risk score calculated (0-100)
   - Recovery potential calculated
7. Results display immediately

#### Step 6: Review Findings
1. Click "Findings" page
2. View all findings from the audit
3. Filter by severity, category, status
4. Click "View Evidence" to see lease/invoice details

#### Step 7: Track Recovery
1. Click "Recovery" page
2. See findings in "Detected" status
3. Click "Dispute" to move to "Disputed"
4. Click "Review" to move to "Under Review"
5. Click "Recover" or "Reject" to finalize

#### Step 8: Generate Dispute
1. Click "Disputes" page
2. Click "Create Dispute" tab
3. Select recovery record
4. Choose template (Standard, Aggressive, Conservative)
5. Click "Create Dispute"
6. View in "View Disputes" tab
7. Export as text file

#### Step 9: View Analytics
1. Click "Analytics" page
2. "Historical Trends" tab:
   - Select property
   - Select metric (Risk Score, Findings Count, Recovery, Recovered Amount)
   - See trends over time
3. "Property Comparison" tab:
   - Select multiple properties
   - Compare metrics side-by-side

#### Step 10: Dashboard Overview
1. Click "Dashboard" page
2. See portfolio KPIs:
   - Total Properties
   - Total Audits
   - Total Findings
   - Potential Recovery
   - Recovered Amount
3. See risk summary and recovery pipeline
4. See high-risk properties alert
5. See recent findings feed

---

## ⚙️ Architecture

### Technology Stack

| Component | Technology | Purpose |
| --- | --- | --- |
| **Frontend** | Streamlit 1.36+ | Web UI, forms, charts |
| **Backend Logic** | Python 3.9+ | Deterministic audit rules |
| **AI Extraction** | RocketRide SDK | Document text extraction |
| **LLM Provider** | Gemini or Groq | Lease/invoice AI parsing |
| **Database** | Supabase PostgreSQL | Data persistence |
| **Auth** | Supabase Auth | User authentication |
| **Visualization** | Plotly 5.0+ | Charts and graphs |
| **Data Processing** | Pandas 2.0+ | DataFrame operations |

### Data Flow

```
User Upload (PDF/TXT)
    ↓
Text Extraction (PyPDF2 or raw text)
    ↓
RocketRide Pipeline
    ↓
LLM (Gemini/Groq)
    ↓
JSON Extraction Result
    ↓
Validation Service (check required fields)
    ↓
Deterministic Audit Engine (Phase 4 business logic)
    ↓
Risk Calculation
    ↓
Recovery Aggregation
    ↓
Supabase Storage
    ↓
Dashboard Display & Analytics
```

### Services

| Service | File | Purpose |
| --- | --- | --- |
| **Authentication** | `services/auth.py` | Supabase Auth wrapper |
| **Audit Engine** | `services/audit_engine.py` | Deterministic lease audit rules |
| **Risk Engine** | `services/risk_engine.py` | Risk score calculation |
| **Recovery Engine** | `services/recovery_engine.py` | Recovery aggregation |
| **Persistence** | `services/supabase_persistence.py` | Supabase data operations |
| **Extraction** | `services/extraction.py` | Sync wrappers for RocketRide |
| **Validation** | `services/validation.py` | Data validation & error checking |
| **Demo Mode** | `services/demo.py` | Sample data generation |
| **AI Pipeline** | `services/ai.py` | RocketRide async functions |

### Pages

| Page | File | Purpose |
| --- | --- | --- |
| **Dashboard** | `pages/dashboard.py` | KPIs, risk summary, recovery tracking |
| **Properties** | `pages/properties.py` | Create, list, manage properties |
| **Documents** | `pages/documents.py` | Upload, extract, manage documents |
| **Audits** | `pages/audits.py` | Run deterministic audits with validation |
| **Findings** | `pages/findings.py` | Filter and review audit findings |
| **Risk Analysis** | `pages/risk_analysis.py` | Portfolio and property risk visualization |
| **Recovery** | `pages/recovery.py` | Recovery pipeline status tracking |
| **Disputes** | `pages/disputes.py` | Dispute generation and management |
| **Analytics** | `pages/analytics.py` | Historical trends and comparisons |
| **Settings** | `pages/settings.py` | User preferences and account management |

---

## 🧪 Testing

### Run All Tests

```bash
pytest tests/ -v
```

All Phase 4 business logic tests should pass:

```
tests/test_audit_engine.py PASSED
tests/test_risk_engine.py PASSED
tests/test_recovery_engine.py PASSED
... (8 tests total)
```

### Validation Checks

```bash
# Python syntax check
python -m py_compile app.py pages/*.py services/*.py ui/*.py

# Import check
python -c "import streamlit; import supabase; import rocketride; print('✓ All imports OK')"

# Streamlit health check
streamlit run app.py --logger.level=error --runner.magicEnabled=false --runner.fastReruns=false
```

### End-to-End Testing

1. **Demo Mode Flow** (5 min):
   ```env
   DEMO_MODE=true
   ```
   - Launch app
   - Sign in
   - View Dashboard
   - View Properties (pre-populated)
   - View Findings (pre-populated)
   - View Analytics (pre-populated)

2. **Manual Workflow** (15 min):
   - Sign in
   - Create property
   - Enter lease data manually
   - Enter invoice data manually
   - Run audit
   - View findings
   - Track recovery status

3. **Document Extraction** (if Gemini/Groq available):
   - Upload actual lease PDF
   - Verify extraction successful
   - Run audit with extracted data

---

## 🛠️ Configuration Reference

### Required Environment Variables

| Variable | Purpose | Example |
| --- | --- | --- |
| `SUPABASE_URL` | Database URL | `https://xxx.supabase.co` |
| `SUPABASE_KEY` | Database API key | `eyJ...` |
| `ROCKETRIDE_GEMINI_KEY` OR `ROCKETRIDE_GROQ_KEY` | AI provider key | `sk-...` or `gsk_...` |

### Optional Environment Variables

| Variable | Purpose | Default |
| --- | --- | --- |
| `DEMO_MODE` | Enable sample data | `false` |
| `ROCKETRIDE_GROQ_BASE_URL` | Groq endpoint | `https://api.groq.com/openai/v1` |
| `SUPABASE_SERVICE_ROLE_KEY` | Admin operations | (not needed) |
| `STREAMLIT_SERVER_HEADLESS` | Headless mode | `true` |

### requirements.txt

All required dependencies:

```
streamlit>=1.36.0          # Web UI
python-dotenv>=1.0.1       # .env loading
supabase>=2.7.0            # Database client
rocketride>=0.1.0          # AI pipeline SDK
plotly>=5.0.0              # Visualization
pandas>=2.0.0              # Data processing
pytest>=7.0.0              # Testing framework
```

---

## 📖 RocketRide Pipeline

### Lease Extraction Pipeline

Located: `pipelines/lease_extraction.pipe`

**Components:**
- Input: Lease document text
- Processor: LLM (Gemini or Groq)
- Output: Extracted lease data as JSON

**Extracted Fields:**
- `base_rent`: Annual base rent
- `cam_cap_pct`: CAM cap as % of base rent
- `tenant_share_pct`: Tenant's share of expenses
- `annual_increase_pct`: Annual rent escalation
- `lease_terms`: Full extracted terms

**Provider Selection:**
1. Try Gemini first (if ROCKETRIDE_GEMINI_KEY set)
2. Fallback to Groq (if ROCKETRIDE_GROQ_KEY set)
3. Return error if neither configured

### Invoice Extraction

Uses the same lease extraction pipeline with invoice-specific prompting.

**Extracted Fields:**
- `cam_expense`: CAM charge on invoice
- `rent_amount`: Rent portion
- `admin_fee_amount`: Administrative fees
- `tax_amount`: Taxes and other charges
- `total_amount`: Total invoice amount

---

## 🔐 Security & Credentials

### Safe credential handling:

✓ Never commit `.env` file
✓ API keys in environment variables only
✓ No hardcoded secrets in source code
✓ Service role key separate from anon key
✓ Database row-level security (RLS) by user_id

### .gitignore protections:

```
.env                    # Do not commit
.venv/                  # Do not commit
__pycache__/            # Do not commit
*.pyc                   # Do not commit
.DS_Store               # Do not commit
```

---

## 🐛 Troubleshooting

### Streamlit Won't Start

```bash
# Clear cache
streamlit cache clear

# Run in verbose mode
streamlit run app.py --logger.level=debug
```

### Supabase Connection Failed

**Error:** `PostgrestError: connection refused`

**Solution:**
- Check SUPABASE_URL and SUPABASE_KEY in .env
- Verify project is active in Supabase Dashboard
- Check firewall/network connectivity

### Extraction Failed

**Error:** `RuntimeError: No LLM provider configured`

**Solution:**
- Set ROCKETRIDE_GEMINI_KEY or ROCKETRIDE_GROQ_KEY
- Restart Streamlit: `streamlit run app.py`

### Validation Errors

**Error:** `Lease validation issues found: base_rent is zero`

**Solution:**
- Ensure extracted data is valid
- Try manual data entry
- Check if extraction confidence is high

---

## 📊 Sample Data

When `DEMO_MODE=true`:

### Properties
- Downtown Office Plaza (San Francisco)
- Retail Shopping Center (Austin)
- Industrial Warehouse (Dallas)

### Audits
- 3 completed audits (one per property)
- 12 total findings (mix of severities)
- 10 recovery records (various statuses)

### Expected Results
- Dashboard: 3 properties, 3 audits, 12 findings
- Risk: Scores ranging 35-75 (mixed risk levels)
- Recovery: ~$15,000 potential recovery (~$6,000 already recovered)

---

## 📞 Support

### Debug Mode

Enable in `.env`:

```env
STREAMLIT_LOGGER_LEVEL=debug
ROCKETRIDE_DEBUG=true
```

Logs will show:
- Extraction requests/responses
- Validation step-by-step
- Audit rule evaluation
- Database operations

### Common Issues

| Issue | Cause | Fix |
| --- | --- | --- |
| Blank dashboard | No data in Supabase | Run demo mode or create property + audit |
| Extraction timeout | Network issue | Increase timeout or use Groq fallback |
| Risk score always 0 | No findings | Audit rules not triggered with your data |
| Recovery shows $0 | No findings created | Ensure audit ran successfully |

---

## 🎯 Success Checklist

- [ ] Environment installed (`python -m venv .venv`)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` configured with at least `SUPABASE_URL`, `SUPABASE_KEY`
- [ ] Supabase project created and schema loaded
- [ ] AI provider key set (Gemini or Groq)
- [ ] `streamlit run app.py` starts without errors
- [ ] Login/Register works
- [ ] Can create a property
- [ ] Can upload documents (or use manual entry)
- [ ] Can run an audit
- [ ] Findings appear on Findings page
- [ ] Dashboard updates with new data
- [ ] Demo mode works (if enabled)

---

## 📝 License

MIT License - See LICENSE file

---

## 🚀 Next Steps (Phase 7+)

Future enhancements:
- Multi-user collaboration and team features
- Automated dispute submission
- Email notifications
- Advanced OCR for image-based documents
- Predictive recovery probability
- Integration with property management systems
- Mobile app
- API endpoint for third-party integration

---

**Version 1.0.0** — Ready for hackathon demonstrations and small-scale production use.

For questions or issues, check the DEBUG logs or review the architecture documentation.

## 6. Run the Streamlit app

```bash
streamlit run app.py
```

Then open the local URL shown in the terminal, usually:

```text
http://localhost:8501
```

## What Supabase Auth handles

Supabase Auth handles:
- email/password user registration
- login and logout
- session management
- authenticated user identity through `auth.users`
- secure password handling without custom password hashing in our app

## What the SQL schema handles

The SQL schema handles the application-owned data for:
- properties
- documents
- audits
- findings
- risk scores
- recovery records
- disputes

It also keeps each record associated with the correct authenticated user and property.

## How `user_id` connects users to their data

Each application table includes a `user_id` column that references `auth.users(id)`.

This means:
- a user signs in with Supabase Auth
- the authenticated user has a UUID in `auth.users`
- our app uses that ID when creating or querying records
- properties, audits, documents, findings, and recovery-related records remain tied to the logged-in user

Example:

- `auth.users.id = 123e...`
- `properties.user_id = 123e...`
- `documents.user_id = 123e...`
- `audits.user_id = 123e...`

That prevents unrelated users from seeing another user's data.

## How to manually run the SQL

Do this in the Supabase dashboard only:

1. Go to SQL Editor.
2. Create a new query.
3. Paste the full contents of `database/schema.sql`.
4. Run it once.
5. Confirm the tables exist.
6. Keep the SQL as a project artifact for future reference.

Do not use the application to create tables automatically. This project intentionally expects the schema to be created by you in the Supabase dashboard.

## Stop here

This project ends at Phase 2. The next phases would cover deeper lease logic, AI processing, pipeline integration, and more advanced app functionality.
