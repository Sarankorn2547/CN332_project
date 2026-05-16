# Food Locker API Reference

## Overview

| Item | Value |
|------|-------|
| Base URL (dev) | `http://localhost:8000` |
| Content-Type | `application/json` |
| Authentication | Bearer JWT — include `Authorization: Bearer <access_token>` header |
| Interactive Docs | `/api/schema/swagger-ui/` (Swagger UI) · `/api/schema/redoc/` (ReDoc) |

### General Error Format

```json
{ "error": "Human-readable error message" }
```

or (DRF standard):

```json
{ "detail": "Human-readable error message" }
```

---

## Authentication

### POST /api/token/

Obtain a JWT access + refresh token pair for a registered LINE user.

**Auth required:** No

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `line_user_id` | string | Yes | LINE user ID (e.g. `Uxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`) |

**Success response — 200 OK:**

```json
{
  "access": "<JWT access token>",
  "refresh": "<JWT refresh token>"
}
```

**Error responses:**

| Status | When |
|--------|------|
| 400 | `line_user_id` not provided |
| 404 | No user with that `line_user_id` exists |

**Example:**

```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"line_user_id": "U123456789"}'
```

---

### POST /api/token/refresh/

Refresh an expired access token using a valid refresh token.

**Auth required:** No

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `refresh` | string | Yes | JWT refresh token obtained from `/api/token/` |

**Success response — 200 OK:**

```json
{
  "access": "<new JWT access token>"
}
```

**Error responses:**

| Status | When |
|--------|------|
| 401 | Refresh token is invalid or expired |

**Example:**

```bash
curl -X POST http://localhost:8000/api/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "<refresh_token>"}'
```

---

## User Management

### POST /api/users/register/

Register a new LINE user and link them to a project, building, and room.

**Auth required:** No

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `line_user_id` | string | Yes | Unique LINE user ID |
| `project_id` | string | Yes | ID of the project (e.g. `prj-001`) |
| `building_id` | string | Yes | ID of the building within that project |
| `room_no` | string | Yes | Room/unit number of the resident |
| `display_name` | string | Yes | Display name from LINE profile |

**Success response — 201 Created:**

```json
{
  "id": 1,
  "line_user_id": "U123456789",
  "project": "prj-001",
  "building": "bld-001",
  "room_no": "101",
  "display_name": "John Doe"
}
```

**Error responses:**

| Status | When |
|--------|------|
| 400 | Any required field is missing |
| 400 | A user with that `line_user_id` already exists |
| 404 | `project_id` does not exist |
| 404 | `building_id` does not exist under that project |

**Example:**

```bash
curl -X POST http://localhost:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "line_user_id": "U123456789",
    "project_id": "prj-001",
    "building_id": "bld-001",
    "room_no": "101",
    "display_name": "John Doe"
  }'
```

---

### GET /api/users/status/

Check whether a LINE user currently has an active (non-AVAILABLE) locker.

**Auth required:** No

**Query parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `line_user_id` | string | Yes | LINE user ID to check |

**Success response — 200 OK (no active locker):**

```json
{
  "status": "NO_ACTIVE_LOCKER",
  "lockers": []
}
```

**Success response — 200 OK (has active locker):**

```json
{
  "status": "HAS_ACTIVE_LOCKER",
  "lockers": [
    {
      "id": "lck-bld001-001",
      "building": "bld-001",
      "local_id": "1",
      "size": "M",
      "status": "BOOKED",
      "type": "FOOD",
      "is_door_open": false,
      "has_object": false,
      "is_locked": true,
      "passcode": "123456",
      "qr_data": "550e8400-e29b-41d4-a716-446655440000",
      "deposit_start_time": null,
      "metadata": null
    }
  ]
}
```

**Error responses:**

| Status | When |
|--------|------|
| 400 | `line_user_id` query parameter not provided |
| 404 | No user with that `line_user_id` exists |

**Example:**

```bash
curl "http://localhost:8000/api/users/status/?line_user_id=U123456789"
```

---

## Lockers

### GET /api/lockers/

List all lockers. Optionally filter by building.

**Auth required:** No

**Query parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `building_id` | string | No | Filter lockers to a specific building |

**Success response — 200 OK:**

```json
[
  {
    "id": "lck-bld001-001",
    "building": "bld-001",
    "local_id": "1",
    "size": "M",
    "status": "AVAILABLE",
    "type": "FOOD",
    "is_door_open": false,
    "has_object": false,
    "is_locked": true,
    "passcode": "",
    "qr_data": "",
    "deposit_start_time": null,
    "metadata": null
  }
]
```

**Example:**

```bash
# All lockers
curl http://localhost:8000/api/lockers/

# Filter by building
curl "http://localhost:8000/api/lockers/?building_id=bld-001"
```

---

### GET /api/lockers/{id}/

Retrieve a single locker by ID.

**Auth required:** No

**Path parameter:** `id` — locker ID string

**Success response — 200 OK:** Same shape as single item from list above.

**Error responses:**

| Status | When |
|--------|------|
| 404 | Locker not found |

**Example:**

```bash
curl http://localhost:8000/api/lockers/lck-bld001-001/
```

---

### PUT /api/lockers/{id}/

Fully update a locker's mutable fields (admin/hardware use).

**Auth required:** Yes (Bearer JWT)

**Path parameter:** `id` — locker ID string

**Request body** (all fields except read-only ones):

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `local_id` | string | Yes | — |
| `size` | string | Yes | e.g. `S`, `M`, `L` |
| `status` | string | Yes | `AVAILABLE`, `BOOKED`, or `OCCUPIED` |
| `type` | string | Yes | e.g. `FOOD` |
| `is_door_open` | boolean | Yes | — |
| `has_object` | boolean | Yes | — |
| `is_locked` | boolean | Yes | — |
| `metadata` | object | No | Optional JSON metadata |

> `id`, `building`, `passcode`, and `qr_data` are read-only and silently ignored if included in the body.

**Success response — 200 OK:** Updated locker object.

**Error responses:**

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT token |
| 404 | Locker not found |

**Example:**

```bash
curl -X PUT http://localhost:8000/api/lockers/lck-bld001-001/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "local_id": "1",
    "size": "L",
    "status": "AVAILABLE",
    "type": "FOOD",
    "is_door_open": false,
    "has_object": false,
    "is_locked": true
  }'
```

---

### PATCH /api/lockers/{id}/

Partially update one or more mutable fields of a locker.

**Auth required:** Yes (Bearer JWT)

**Request body:** Any subset of the PUT fields above.

**Success response — 200 OK:** Updated locker object.

**Example:**

```bash
curl -X PATCH http://localhost:8000/api/lockers/lck-bld001-001/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"size": "S"}'
```

---

## Locker Workflow Actions

The complete delivery flow is: **book → open → deposit → verify-qr → pickup**.

### POST /api/lockers/book/

Find and book an available locker by building, size, and type. Generates a QR code and passcode.

**Auth required:** Yes (Bearer JWT)

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `building_id` | string | Yes | ID of the building to search in |
| `size` | string | Yes | Desired locker size (e.g. `S`, `M`, `L`) |
| `type` | string | Yes | Locker type (e.g. `FOOD`) |

**Success response — 200 OK:**

```json
{
  "locker_id": "lck-bld001-001",
  "qr_data": "550e8400-e29b-41d4-a716-446655440000",
  "passcode": "847291"
}
```

**Error responses:**

| Status | When |
|--------|------|
| 400 | Missing required field |
| 400 | No AVAILABLE locker found matching the criteria |
| 401 | Missing or invalid JWT token |

**Example:**

```bash
curl -X POST http://localhost:8000/api/lockers/book/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"building_id": "bld-001", "size": "M", "type": "FOOD"}'
```

---

### POST /api/lockers/{id}/open/

Unlock and open the door of a BOOKED or OCCUPIED locker (used by the rider before depositing food).

**Auth required:** Yes (Bearer JWT)

**Path parameter:** `id` — locker ID

**Request body:** None

**Success response — 200 OK:** Updated locker object with `is_door_open: true`, `is_locked: false`.

**Error responses:**

| Status | When |
|--------|------|
| 400 | Locker not found or not in BOOKED/OCCUPIED status |
| 401 | Missing or invalid JWT token |

**Example:**

```bash
curl -X POST http://localhost:8000/api/lockers/lck-bld001-001/open/ \
  -H "Authorization: Bearer <access_token>"
```

---

### POST /api/lockers/{id}/deposit/

Confirm that the rider has placed food in the locker. Transitions status from BOOKED to OCCUPIED. The door must already be open.

**Auth required:** Yes (Bearer JWT)

**Path parameter:** `id` — locker ID

**Request body:** None

**Success response — 200 OK:** Updated locker object with `status: "OCCUPIED"`, `has_object: true`, `is_door_open: false`, `is_locked: true`.

**Error responses:**

| Status | When |
|--------|------|
| 400 | Locker not found, not in BOOKED status, or door is not open |
| 401 | Missing or invalid JWT token |

**Example:**

```bash
curl -X POST http://localhost:8000/api/lockers/lck-bld001-001/deposit/ \
  -H "Authorization: Bearer <access_token>"
```

---

### POST /api/lockers/verify-qr/

Verify the customer's QR code or passcode and open the locker. The locker must be OCCUPIED.

**Auth required:** Yes (Bearer JWT)

**Request body** (provide at least one):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `qr_data` | string | No | QR code data string from the booking |
| `passcode` | string | No | 6-digit passcode from the booking |

**Success response — 200 OK:** Updated locker object with `is_door_open: true`, `is_locked: false`.

**Error responses:**

| Status | When |
|--------|------|
| 400 | Neither `qr_data` nor `passcode` provided |
| 400 | QR/passcode does not match any OCCUPIED locker |
| 401 | Missing or invalid JWT token |

**Example:**

```bash
# Using QR data
curl -X POST http://localhost:8000/api/lockers/verify-qr/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"qr_data": "550e8400-e29b-41d4-a716-446655440000"}'

# Using passcode
curl -X POST http://localhost:8000/api/lockers/verify-qr/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"passcode": "847291"}'
```

---

### POST /api/lockers/{id}/pickup/

Confirm that the customer has retrieved the food. Resets the locker to AVAILABLE.

**Auth required:** Yes (Bearer JWT)

**Path parameter:** `id` — locker ID

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `actor_id` | string | No | Identifier of who performed pickup (default: `"customer"`) |

**Success response — 200 OK:** Updated locker object with `status: "AVAILABLE"`, `has_object: false`, `passcode: ""`, `qr_data: ""`.

**Error responses:**

| Status | When |
|--------|------|
| 400 | Locker not found or not in OCCUPIED status |
| 401 | Missing or invalid JWT token |

**Example:**

```bash
curl -X POST http://localhost:8000/api/lockers/lck-bld001-001/pickup/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"actor_id": "customer"}'
```

---

## Master Data

### GET /api/projects/

List all projects.

**Auth required:** No

**Success response — 200 OK:**

```json
[
  {
    "id": "prj-001",
    "name": "Sukhumvit Residence",
    "address": "123 Sukhumvit Rd, Bangkok",
    "metadata": null
  }
]
```

**Example:**

```bash
curl http://localhost:8000/api/projects/
```

---

### GET /api/buildings/

List all buildings. Optionally filter by project.

**Auth required:** No

**Query parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | No | Filter to buildings within a project |

**Success response — 200 OK:**

```json
[
  {
    "id": "bld-001",
    "project": "prj-001",
    "name": "Building A",
    "metadata": null
  }
]
```

**Example:**

```bash
curl "http://localhost:8000/api/buildings/?project_id=prj-001"
```

---

### GET /api/rooms/

List all rooms. Optionally filter by building.

**Auth required:** No

**Query parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `building_id` | string | No | Filter to rooms within a building |

**Success response — 200 OK:**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "building": "bld-001",
    "unit_number": "101",
    "floor": "1"
  }
]
```

**Example:**

```bash
curl "http://localhost:8000/api/rooms/?building_id=bld-001"
```

---

## LINE Integration

### POST /api/line/webhook/

Receive webhook events from the LINE Messaging API platform. Validates the request using HMAC-SHA256 signature.

**Auth required:** No (signature-based validation via `X-Line-Signature` header)

**Headers:**

| Header | Required | Description |
|--------|----------|-------------|
| `X-Line-Signature` | Yes | Base64-encoded HMAC-SHA256 of request body using `LINE_CHANNEL_SECRET` |

**Request body:** LINE webhook payload (set by LINE platform, not the developer).

**Success response — 200 OK:**

```json
{ "status": "ok" }
```

**Error responses:**

| Status | When |
|--------|------|
| 401 | Signature is missing or does not match |

---

### POST /api/line/push/

Send a text message, an image, or both to a LINE user via the LINE Messaging API.

**Auth required:** Yes (Bearer JWT)

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `to` | string | Yes | LINE user ID of the recipient |
| `message` | string | No* | Text message to send |
| `image_url` | string | No* | Publicly accessible URL of an image to send |

> *At least one of `message` or `image_url` must be provided.

**Success response — 200 OK:**

```json
{ "status": "ok", "result": {} }
```

**Error responses:**

| Status | When |
|--------|------|
| 400 | `to` is missing |
| 400 | Neither `message` nor `image_url` provided |
| 401 | Missing or invalid JWT token |
| 500 | LINE API returned an error |

**Example:**

```bash
# Send text
curl -X POST http://localhost:8000/api/line/push/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"to": "U123456789", "message": "Your food is ready for pickup!"}'

# Send image
curl -X POST http://localhost:8000/api/line/push/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"to": "U123456789", "image_url": "https://example.com/food.jpg"}'

# Send text + image
curl -X POST http://localhost:8000/api/line/push/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "U123456789",
    "message": "Your food is in locker 3A. Passcode: 847291",
    "image_url": "https://example.com/qr.jpg"
  }'
```
