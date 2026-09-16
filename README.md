# OpenMail Verify

**Open-Source Email Validation & Deliverability Intelligence Platform**

OpenMail Verify is a full-stack, production-grade email verification application engineered to inspect email syntax, domain infrastructure, DNS resolution, MX mail exchanges, disposable mailbox providers, and corporate role-based aliases.

Designed with a restrained, human-crafted **White and Navy Blue** interface, OpenMail Verify eliminates bloated AI-generated visual clutter in favor of typographic hierarchy, information density, and real-time infrastructure metrics.

---

## Table of Contents
- [Overview & Objectives](#overview--objectives)
- [Architecture & Verification Pipeline](#architecture--verification-pipeline)
- [Design Philosophy](#design-philosophy)
- [Technology Stack](#technology-stack)
- [Open-Source Libraries & Dependencies](#open-source-libraries--dependencies)
- [API Documentation](#api-documentation)
- [Installation & Setup](#installation--setup)
- [Environment Variables](#environment-variables)
- [Running Locally](#running-locally)
- [Testing](#testing)
- [Technical Limitations](#technical-limitations)
- [Security Considerations](#security-considerations)
- [License](#license)

---

## Overview & Objectives

### The Problem
Traditional client-side email validation often relies purely on simplistic regular expressions (`regex`), which verify only that an input string roughly resembles an email address. This fails to detect:
- Non-existent or expired domain names
- Domains with no active mail servers (missing MX records)
- Temporary/burner email addresses that lead to high bounce rates
- Shared corporate role aliases (`support@`, `sales@`, `billing@`)

### Objectives
1. **Multi-layer Pipeline**: Inspect email addresses through RFC 5322 compliance, DNS resolution, MX records, disposable domain detection, and role alias matching.
2. **Transparent Scoring**: Calculate an inspection score (0–100) based on clear, deterministic rules without misleading claims of guaranteed deliverability.
3. **Audit History & Batch Verification**: Support bulk auditing (up to 50 emails) with live progress tracking, SQLite-backed persistent audit history, and CSV export.
4. **Developer-Friendly REST API**: Provide clean JSON endpoints, OpenAPI (Swagger) documentation, and code samples for cURL, Python, and JavaScript.

---

## Architecture & Verification Pipeline

```
                                 [ Incoming Email ]
                                          │
                                 ┌────────┴────────┐
                                 │ 1. Syntax Check │ ──(RFC 5322 & Unicode)
                                 └────────┬────────┘
                                          │
                                 ┌────────┴────────┐
                                 │ 2. Normalization│ ──(Extract Domain & Local-part)
                                 └────────┬────────┘
                                          │
                                 ┌────────┴────────┐
                                 │ 3. DNS Lookup   │ ──(Resolve A / AAAA IP records)
                                 └────────┬────────┘
                                          │
                                 ┌────────┴────────┐
                                 │ 4. MX Discovery │ ──(Retrieve Hostnames & Priorities)
                                 └────────┬────────┘
                                          │
                                 ┌────────┴────────┐
                                 │ 5. Risk Signals │ ──(Disposable & Role-Based Match)
                                 └────────┬────────┘
                                          │
                                 ┌────────┴────────┐
                                 │ 6. Score Engine │ ──(Compute 0-100 Score & Status)
                                 └────────┬────────┘
                                          │
                           ┌──────────────┴──────────────┐
                           ▼                             ▼
                  [ SQLite Audit Log ]          [ JSON API Response ]
```

### Result Classification:
- **`VALID`**: Conforms to RFC 5322, domain resolves, active MX records found, not disposable, not a role alias.
- **`RISKY`**: Valid domain/MX, but identified as a disposable/burner email or shared role-based inbox.
- **`INVALID`**: Syntax invalid, non-existent domain (NXDOMAIN), or no mail server configured.
- **`UNKNOWN`**: External DNS query timeout or temporary network failure.

### Score Breakdown (0–100):
- **Syntax Validation**: 20 points
- **Domain DNS Resolution**: 20 points
- **MX Record Presence**: 25 points
- **Non-Disposable Domain**: 20 points
- **Non-Role-Based Address**: 15 points

---

## Design Philosophy

The frontend interface is built with strict human-designed SaaS aesthetics:
- **Palette**: Pure White (`#FFFFFF`) canvas, Navy Blue (`#0F172A` / `#1E3A8A`) for headings, primary buttons, and active tabs, and Dark Slate/Black (`#0F172A` / `#334155`) for readable content.
- **Typography**: Inter for primary UI elements and JetBrains Mono for email addresses, domains, IP records, and MX hostnames.
- **Restraint**: Zero AI-style neon gradients, glassmorphism, floating decorative particles, or cards-in-cards.

---

## Technology Stack

### Backend
- **Python 3.10+**
- **FastAPI**: High-performance asynchronous REST API framework
- **Pydantic v2**: Strict data validation and schema enforcement
- **SQLAlchemy 2.0**: ORM for persistent audit log tracking
- **SQLite**: Zero-configuration embedded database
- **pytest & httpx**: Automated test execution and API mocking

### Frontend
- **React 18**: UI component architecture
- **Vite 5**: Fast build tooling and hot module replacement (HMR)
- **Tailwind CSS**: Utility-first styling with custom Navy/White design tokens
- **Lucide React**: Clean, lightweight, consistent open-source iconography
- **Recharts**: Clean, restrained data visualization
- **Axios**: HTTP API client with centralized error interception

---

## Open-Source Libraries & Dependencies

| Library | Version | License | Role in Project |
| :--- | :--- | :--- | :--- |
| **`email-validator`** | `2.1.1` | MIT | RFC 5322 syntax validation, internationalized domain name (IDN) handling, and normalization. |
| **`dnspython`** | `2.6.1` | ISC | Direct DNS queries for MX, A, and AAAA records with custom timeout control. |
| **`fastapi`** | `0.110.0` | MIT | Core web API framework, dependency injection, and automatic OpenAPI schema generation. |
| **`sqlalchemy`** | `2.0.28` | MIT | Database session management and ORM for SQLite audit logging. |
| **`pydantic`** | `2.6.4` | MIT | Request and response schema modeling and serializing. |
| **`lucide-react`** | `0.359.0` | ISC | Professional, minimalist iconography. |
| **`recharts`** | `2.12.3` | MIT | SVG-based charting for verification distribution. |
| **`tailwindcss`** | `3.4.1` | MIT | Design system implementation. |

---

## API Documentation

### 1. Verify Single Email
`POST /api/v1/verify`

**Request:**
```json
{
  "email": "alex.doe@gmail.com"
}
```

**Response (`200 OK`):**
```json
{
  "email": "alex.doe@gmail.com",
  "normalized_email": "alex.doe@gmail.com",
  "domain": "gmail.com",
  "status": "VALID",
  "score": 95,
  "checks": {
    "syntax": { "passed": true, "status": "passed", "message": "Email conforms to RFC 5322 syntax standards" },
    "domain": { "passed": true, "status": "passed", "message": "Domain 'gmail.com' is syntactically valid" },
    "dns": { "passed": true, "status": "passed", "message": "Domain resolved successfully (1 IP record found)." },
    "mx": { "passed": true, "status": "passed", "message": "5 MX records detected (Primary: gmail-smtp-in.l.google.com)." },
    "disposable": { "passed": true, "status": "passed", "message": "Domain is not identified as a temporary/disposable inbox." },
    "role_based": { "passed": true, "status": "passed", "message": "Address is individual/personal, not a generic role alias." },
    "free_provider": { "passed": true, "status": "info", "message": "Domain is hosted by major consumer provider (gmail.com)." }
  },
  "domain_intelligence": {
    "domain": "gmail.com",
    "is_resolvable": true,
    "mx_records": [
      { "priority": 5, "host": "gmail-smtp-in.l.google.com" },
      { "priority": 10, "host": "alt1.gmail-smtp-in.l.google.com" }
    ],
    "a_records": ["142.250.190.37"],
    "is_disposable": false,
    "is_free_provider": true,
    "has_mail_server": true
  },
  "message": "Email passed all available syntax, DNS resolution, and mail server (MX) checks."
}
```

### 2. Batch Verification
`POST /api/v1/verify/batch`
- Accepts an array of up to 50 email strings.
- Returns aggregated counts (`valid_count`, `invalid_count`, `risky_count`, `average_score`) and itemized results.

### 3. History & Analytics
- `GET /api/v1/history?page=1&page_size=20&status=VALID&search=query`: Paginated audit log.
- `DELETE /api/v1/history`: Clears audit records.
- `GET /api/v1/stats`: Summary counts and deliverability percentages.

---

## Installation & Setup

### Prerequisites
- Python 3.10 or higher
- Node.js 18+ and npm

### 1. Clone Repository
```bash
git clone https://github.com/your-org/openmail-verify.git
cd "openmail-verify"
```

### 2. Backend Setup
```bash
# Install Python dependencies
pip install -r backend/requirements.txt
```

### 3. Frontend Setup
```bash
cd frontend
npm install
cd ..
```

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env` if custom configuration is desired:

```env
PROJECT_NAME="OpenMail Verify API"
API_V1_STR="/api/v1"
DATABASE_URL="sqlite:///./verification_history.db"
ENABLE_HISTORY_LOGGING=true
DNS_TIMEOUT_SECONDS=3.0
DNS_LIFETIME_SECONDS=5.0
MAX_BATCH_SIZE=50
```

---

## Running Locally

### Start Backend API Server
```bash
# From workspace root
$env:PYTHONPATH="backend" # Windows PowerShell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
API runs on `http://127.0.0.1:8000` (Interactive docs available at `http://127.0.0.1:8000/docs`).

### Start Frontend Dev Server
```bash
cd frontend
npm run dev
```
Frontend runs on `http://localhost:5173/`.

---

## Testing

Run the automated test suite covering syntax rules, DNS resolution logic, score calculators, disposable lists, role prefixes, and REST endpoints:

```bash
$env:PYTHONPATH="backend"
python -m pytest backend/tests -v
```

---

## Technical Limitations

1. **Mailbox Existence and Obscured Verification**: Mailbox existence cannot be guaranteed for every provider. Some mail providers intentionally block, greylist, or obscure recipient verification. In such cases, MailScope returns `UNKNOWN` instead of making an unsupported `VALID` or `INVALID` claim.
2. **Deliverability vs Infrastructure Verification**: Technical verification confirms syntax, domain infrastructure, DNS resolution, MX records, and absence of high-risk flags. To confirm actual end-to-end access to an active mailbox, utilize the interactive Mailbox Challenge OTP verification flow.

---

## Security Considerations

- **Input Sanitization**: All incoming email strings are stripped, length-checked, and validated against standard email grammars before DNS operations.
- **DNS Timeouts**: dnspython resolver timeout is capped at 3.0 seconds to prevent denial-of-service or socket starvation.
- **Privacy**: No plaintext credentials or external third-party tracking cookies are used. History logging can be toggled off via `ENABLE_HISTORY_LOGGING=false`.

---

## License

This project is open-source software licensed under the [MIT License](LICENSE).
