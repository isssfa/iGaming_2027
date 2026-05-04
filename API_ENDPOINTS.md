# API endpoints reference

Base URL for all routes below: **`/api/`** (see `iGamingForms/urls.py` → `api/`).

Example full URL on local dev: `http://localhost:8000/api/register/`

---

## Authentication and CSRF

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/security/csrf-token/` | Obtain a CSRF token for protected `POST` requests |

**POST** endpoints that use `ProtectedPostPermission` (including **`/api/register/`** and **`/api/inquiry/`**) must send the token in one of:

- Header: `X-CSRF-Token: <token>` (or `X-Csrf-Token`)
- JSON body field: `csrf_token`
- Query string: `?csrf_token=<token>` (fallback)

With `credentials: 'include'`, the browser session cookie is used together with the token as expected by Django.

**CORS:** Allowed origins are configured in `iGamingForms/settings.py` (`CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`).

---

## 1. Event registration (operator & interest forms)

| Method | Endpoint | Permission |
|--------|----------|------------|
| `POST` | `/api/register/` | CSRF + rate limit (default `10/m`) |

Single endpoint; behaviour is determined by **`type`** or inferred from **`products`** vs **`interests`**.

### 1a. Operator registration (`type: "operator"`)

**Required fields:** `firstName`, `lastName`, `email`, `phone`, `nationality`, `company`, `weburl`, `jobTitle`, `jobLevel`, `companyOperation`, `brands` (non-empty array), `products` (non-empty array of valid product IDs).

**Not allowed:** `interests`.

**Phone:** international format — must start with `+` followed by digits only (e.g. `+254712345678`).

**Payload example:**

```json
{
  "type": "operator",
  "firstName": "Jane",
  "lastName": "Doe",
  "email": "jane@example.com",
  "phone": "+254712345678",
  "nationality": "Kenyan",
  "company": "Acme Gaming Ltd",
  "weburl": "https://acmegaming.com",
  "jobTitle": "Marketing Manager",
  "jobLevel": "Mid-Senior Level",
  "companyOperation": "Operator",
  "brands": ["Brand One", "Brand Two"],
  "products": ["online-casino", "sportsbook"]
}
```

**`type` optional:** If omitted, sending **`products`** infers `operator`.

**`jobLevel` allowed values:**

`Entry Level`, `Associate`, `Mid-Senior Level`, `Director`, `Executive`, `C-Suite`, `Owner/Partner`, `Intern`, `Other`

**`companyOperation` allowed values:**

`Operator`, `Affiliate`, `Investor`, `Media`, `Regulator`, `Non-profit`, `Sports Organisation`, `Supplier/Service Provider`

**`products` allowed IDs:**

`online-casino`, `sportsbook`, `hybrid`, `esports-betting`, `fantasy-sports`, `poker`, `bingo`, `ilottery`, `sweepstake-casino`, `social-casino`, `landbased-casino`, `retail-betting-shop`

**cURL example (two-step: CSRF then register):**

```bash
# 1) Get CSRF token (adjust host/port)
TOKEN=$(curl -s -c cookies.txt http://localhost:8000/api/security/csrf-token/ | jq -r '.csrf_token')

# 2) Register (send token header; use cookies if session-based)
curl -s -b cookies.txt -c cookies.txt \
  -X POST http://localhost:8000/api/register/ \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: $TOKEN" \
  -d '{
    "type": "operator",
    "firstName": "Jane",
    "lastName": "Doe",
    "email": "jane@example.com",
    "phone": "+254712345678",
    "nationality": "Kenyan",
    "company": "Acme Gaming Ltd",
    "weburl": "https://acmegaming.com",
    "jobTitle": "Marketing Manager",
    "jobLevel": "Mid-Senior Level",
    "companyOperation": "Operator",
    "brands": ["Brand One", "Brand Two"],
    "products": ["online-casino", "sportsbook"]
  }'
```

**Success:** `201 Created` — body typically `{"message": "Registration successful."}`

**Errors:** `400` with field-level validation errors; `403` if CSRF/origin/rate limit fails.

---

### 1b. Interest registration (`type: "interest"`)

**Required fields:** `firstName`, `lastName`, `email`, `phone`, `nationality`, `company`, `jobTitle`, `jobLevel`, `companyOperation`, `interests` (non-empty array of valid interest IDs).

**Not allowed:** `weburl`, `brands`, `products`.

**Payload example:**

```json
{
  "type": "interest",
  "firstName": "John",
  "lastName": "Smith",
  "email": "john@example.com",
  "phone": "+254798765432",
  "nationality": "Ugandan",
  "company": "Media House Ltd",
  "jobTitle": "Editor",
  "jobLevel": "Director",
  "companyOperation": "Media",
  "interests": ["exhibiting", "sponsoring"]
}
```

**`type` optional:** If omitted and **`products`** is not sent, **`interests`** infers `interest`.

**`interests` allowed IDs:** `exhibiting`, `sponsoring`, `attending`

**cURL example:**

```bash
TOKEN=$(curl -s -c cookies.txt http://localhost:8000/api/security/csrf-token/ | jq -r '.csrf_token')

curl -s -b cookies.txt -c cookies.txt \
  -X POST http://localhost:8000/api/register/ \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: $TOKEN" \
  -d '{
    "type": "interest",
    "firstName": "John",
    "lastName": "Smith",
    "email": "john@example.com",
    "phone": "+254798765432",
    "nationality": "Ugandan",
    "company": "Media House Ltd",
    "jobTitle": "Editor",
    "jobLevel": "Director",
    "companyOperation": "Media",
    "interests": ["exhibiting", "sponsoring"]
  }'
```

---

## 2. Inquiry (existing)

| Method | Endpoint | Permission |
|--------|----------|------------|
| `POST` | `/api/inquiry/` | CSRF + rate limit |

**Body fields:** `name`, `email`, `topic`, `message`

**Example:**

```bash
TOKEN=$(curl -s -c cookies.txt http://localhost:8000/api/security/csrf-token/ | jq -r '.csrf_token')

curl -s -b cookies.txt -c cookies.txt \
  -X POST http://localhost:8000/api/inquiry/ \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: $TOKEN" \
  -d '{"name":"Ada","email":"ada@example.com","topic":"Partnership","message":"Hello"}'
```

---

## 3. Event schedule (panels)

| Method | Endpoint | Permission |
|--------|----------|------------|
| `GET` | `/api/schedule/` | Public (`AllowAny`) |

Returns a **JSON array** of panels. Each item includes moderator and linked speakers (from the `speakers` app). Moderator and panel speakers must exist as `Speaker` records in admin.

**Response shape (per panel):**

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Panel primary key |
| `panelName` | string | Panel title |
| `description` | string \| null | Panel description |
| `time` | ISO 8601 datetime | Start time (timezone-aware) |
| `location` | string | Venue / room |
| `moderator` | object | `{ id, name, role, company, image }` |
| `speakers` | array | Same object shape as moderator |

**Example:**

```bash
curl -s http://localhost:8000/api/schedule/
```

---

## 4. Exhibitors list

| Method | Endpoint | Permission |
|--------|----------|------------|
| `GET` | `/api/exhibition/exhibitors/` | Public (`AllowAny`) |

Returns **active** exhibitors only (`is_active=True` in admin).

**Response shape (per exhibitor):**

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Exhibitor name |
| `description` | string \| null | Long text |
| `image` | string \| null | Absolute URL to uploaded image |
| `website` | string \| null | Website URL |
| `social` | object | Only non-empty keys among `twitter`, `linkedin`, `instagram`, `facebook` |
| `standInformation` | string \| null | Booth / stand code (e.g. `E02`) |

**Example:**

```bash
curl -s http://localhost:8000/api/exhibition/exhibitors/
```

**Related:** Exhibition tiers/options (existing): `GET /api/exhibition/`

---

## 5. Sponsors (grouped list + social links)

| Method | Endpoint | Permission |
|--------|----------|------------|
| `GET` | `/api/sponsors/` | Public (`AllowAny`) |

Response is a **grouped object** (headline, diamond, platinum, etc.). Each sponsor entry now includes:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Sponsor name |
| `logo` | string \| null | Absolute URL |
| `url` | string \| null | Main website |
| `social` | object | Optional nested links: `twitter`, `linkedin`, `instagram`, `facebook` (omitted keys if empty) |

**Example:**

```bash
curl -s http://localhost:8000/api/sponsors/
```

---

## 6. Tickets

| Method | Endpoint | Permission |
|--------|----------|------------|
| `GET` | `/api/tickets/` | Public (`AllowAny`) |

Returns **active** tickets (`is_active=True`), ordered by price then label.

**Response shape (per ticket):**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Stripe price id (stored as `stripe_price_id`) |
| `label` | string | Display name (e.g. `VVIP`) |
| `price` | decimal | Current / base price |
| `doorPrice` | decimal \| null | Door price |
| `isPopular` | boolean | Highlight flag |
| `description` | string \| null | Short description |
| `features` | string[] | List of feature strings (from newline-separated admin text) |
| `priceIncreaseDate` | ISO 8601 datetime \| null | When price increases |

**Example:**

```bash
curl -s http://localhost:8000/api/tickets/
```

**Example JSON item (illustrative):**

```json
{
  "id": "price_1Sc3xlCBe8Ewb1SihYH6Okgn",
  "label": "VVIP",
  "price": "670.00",
  "doorPrice": "950.00",
  "isPopular": true,
  "description": "Luxury experience",
  "features": [
    "Welcome Reception",
    "Full Expo Access"
  ],
  "priceIncreaseDate": "2026-06-01T00:00:00+03:00"
}
```

---

## Quick reference table

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/security/csrf-token/` | CSRF token for protected POSTs |
| `POST` | `/api/register/` | Operator or interest registration |
| `POST` | `/api/inquiry/` | General inquiry |
| `GET` | `/api/schedule/` | Panels with moderator and speakers |
| `GET` | `/api/exhibition/` | Exhibition tiers/options (existing) |
| `GET` | `/api/exhibition/exhibitors/` | Exhibitor directory |
| `GET` | `/api/sponsors/` | Sponsors grouped by tier/type + social |
| `GET` | `/api/tickets/` | Ticket tiers / pricing for frontend |

---

## Admin: content management

- **Panels & tickets:** Django admin → `base` → `Panel`, `Ticket`
- **Exhibitors:** Django admin → `exhibition` → `Exhibitor`
- **Sponsors (incl. social URLs):** Django admin → `sponsor` → `Sponsor`
- **Speakers:** Django admin → `speakers` → `Speaker` (linked from panels)

---

## Frontend fetch examples (browser)

**GET (no CSRF):**

```javascript
const res = await fetch("https://your-api-host/api/schedule/");
const panels = await res.json();
```

**POST register (with CSRF from your security endpoint):**

```javascript
const csrfRes = await fetch("https://your-api-host/api/security/csrf-token/", {
  credentials: "include",
});
const { csrf_token } = await csrfRes.json();

await fetch("https://your-api-host/api/register/", {
  method: "POST",
  credentials: "include",
  headers: {
    "Content-Type": "application/json",
    "X-CSRF-Token": csrf_token,
  },
  body: JSON.stringify({
    type: "operator",
    firstName: "Jane",
    lastName: "Doe",
    email: "jane@example.com",
    phone: "+254712345678",
    nationality: "Kenyan",
    company: "Acme Gaming Ltd",
    weburl: "https://acmegaming.com",
    jobTitle: "Marketing Manager",
    jobLevel: "Mid-Senior Level",
    companyOperation: "Operator",
    brands: ["Brand One", "Brand Two"],
    products: ["online-casino", "sportsbook"],
  }),
});
```

Replace `https://your-api-host` with your deployed API origin (must be allowed in CORS/CSRF settings).
