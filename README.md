# Meet Manager

**Meet Manager** הוא מערכת ניהול ועידות פנים-ארגונית מבוססת הרשאות תפקיד.  
המערכת מאפשרת לאדמינים לנהל מדורים, משתמשים וחדרי ועידה וירטואליים — עם בקרת גישה מפורטת ברמת המדור.

המערכת מבוססת על **CMS-First Architecture** — הפגישות חיות אך ורק בשרתי Cisco Meeting Server (CMS), וה-DB משמש כ-overlay לנתוני הרשאות, מדורים, ומועדפים. הבקאנד מתחבר לשני שרתי CMS — אחד ל-Audio ואחד ל-Video — לצורך יצירת CoSpaces, ניהול סיסמאות, ומעקב אחר שיחות חיות.

---

## Table of Contents

1. [Tech Stack](#tech-stack)
2. [Architecture](#architecture)po
3. [Project Structure](#project-structure)
4. [Getting Started](#getting-started)
5. [Environment Variables](#environment-variables)
6. [CI/CD](#cicd)
7. [Production Deployment](#production-deployment)
8. [Roles & Permissions](#roles--permissions)
9. [Admin Access Levels](#admin-access-levels)
10. [Access Level System](#access-level-system)
11. [API Reference](#api-reference)
12. [Database Schema](#database-schema)
13. [Frontend Pages](#frontend-pages)
14. [Authentication Flow](#authentication-flow)
15. [Logging System](#logging-system)
16. [Security](#security)
17. [CMS Integration](#cms-integration)
18. [Dual CMS Architecture](#dual-cms-architecture)
19. [Data Persistence & Backups](#data-persistence--backups)

---

## Tech Stack

| Layer            | Technology                                    |
| ---------------- | --------------------------------------------- |
| Frontend         | React 19, Vite 7, React Router 7, Axios 1.6   |
| Backend          | FastAPI 0.135, SQLAlchemy, Pydantic v2, requests 2.32 |
| Database         | PostgreSQL 15                                 |
| Auth             | JWT (PyJWT, HS256, 24h expiry)                |
| Passwords        | Argon2 (via passlib)                          |
| Containerization | Docker + Docker Compose + Nginx               |
| Logging          | Custom async queue-based rotating file logger |
| CI/CD            | GitHub Actions                                |

---

## Architecture

```
Development (Docker Compose)
Browser (React/Vite → host port :3000)
  │
  │  HTTP + JWT session cookies
  ▼
FastAPI Backend (:8001, mapped to container port 8000)
  │
  ├── SQLAlchemy ORM ──► PostgreSQL (:5432)  [users / groups / permissions / favorites]
  │                                               (overlay data only)
  │
  ├── HTTP ────────────► CMS Audio Server (https://192.168.20.200:445/api/v1)
  │                       [audio CoSpaces + live calls + passwords]
  │
  └── HTTP ────────────► CMS Video Server (https://192.168.20.201:445/api/v1)
                          [video CoSpaces + live calls + passwords]

Production (standalone stack)
Browser
  │
  │  HTTP
  ▼
Nginx :3000  (serves React build + reverse proxy)
  │
  ├── /              -> React static build
  └── /auth|users|groups|meetings|protected|favorites|servers|logs -> FastAPI :8000
          │
          ├── meet-db (PostgreSQL, internal Docker network)
          ├── CMS Audio Server (external, configured via CMS_AUDIO_URL)
          └── CMS Video Server (external, configured via CMS_VIDEO_URL)
```

In **development**, the Vite dev server runs inside Docker, exposed on host port `:3000` (remapped from container port `:5173` due to WSL2 networking). The backend is accessible on host port `:8001`.

### CMS-First Architecture

The system now uses a **CMS-First Architecture**:

- **Meetings live in CMS only** — CoSpaces are the single source of truth for meeting data
- **Database is an overlay** — stores only:
  - User permissions and group memberships
  - Meeting-to-group associations (via `GroupMeeting` table)
  - User favorites (via `FavoriteMeeting` table)
- **Write-through pattern** — create/update/delete operations automatically sync to CMS
- **Read-through pattern** — meeting data is fetched from CMS and enriched with overlay data

The **dual CMS** setup routes all audio meetings to the audio CMS server and all video meetings to the video CMS server. `blast_dial` meetings are excluded from CMS interactions entirely (not yet supported).

---

## Project Structure

```
meet/
├── docker-compose.yml              # Standalone dev/prod stack (own DB + Census API)
├── docker-compose.prod.yml         # Production build stack (builds images from source)
├── docker-compose-ssot.yml         # SSOT stack (shared census-db over ssot-net)
├── .env                            # Local development env (not committed)
├── .env.prod.example               # Production env template
├── workflows/
│   ├── ci.yml                      # CI pipeline (lint + test)
│   └── deploy-ubuntu.yml           # Deploy to Ubuntu over SSH
├── initdb/
│   └── 01_restore.sql              # DB snapshot loaded on first init
├── Backend/
│   ├── Dockerfile.backend          # Development backend image
│   ├── Dockerfile.prod             # Production backend image
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── tests/                      # Backend test suite
│   ├── main.py                     # App entry point, lifespan, CORS, routers
│   ├── logger.py                   # Async rotating daily log system
│   ├── alembic/                    # DB migration scripts
│   └── app/
│       ├── core/
│       ├── models/
│       ├── repository/
│       ├── routers/
│       ├── schema/
│       ├── security/
│       ├── service/
│       └── util/
└── Frontend/
    ├── Dockerfile                  # Development frontend image
    ├── Dockerfile.prod             # Production frontend image (Vite build + Nginx)
    ├── nginx.conf                  # Nginx SPA + API reverse proxy config
    ├── package.json
    └── src/
        ├── components/
        ├── context/
        ├── mocks/                  # Local mock CMS data
        ├── pages/
        └── services/
            └── api.js              # Axios client + CMS mode switching
```

---

## Getting Started

### Prerequisites

- Docker Desktop (or Docker Engine on Linux) running
- `.env` file in the project root (see [Environment Variables](#environment-variables))
- CMS server(s) reachable at the configured URLs (see [Environment Variables](#environment-variables))

### Run the standalone stack

```bash
docker compose up --build
```

| Service            | URL                         |
| ------------------ | --------------------------- |
| Frontend           | http://localhost:5173       |
| Backend API        | http://localhost:8001       |
| API Docs (Swagger) | http://localhost:8001/docs  |

### Run the SSOT stack (shared Census DB)

Requires the external `ssot-net` Docker network to exist:

```bash
docker network create ssot-net   # once, on the server
docker compose -f docker-compose-ssot.yml up -d
```

### Stop the stack

```bash
docker compose down
```

> `docker compose down` does **not** delete the database volume. To also remove the volume: `docker compose down -v`

### Rebuild only the frontend

```bash
docker compose build frontend
docker compose up -d frontend
```

### Default super admin login

| Field    | Value                |
| -------- | -------------------- |
| s_id     | `admin`              |
| Password | `1234`               |

> These values come from `docker-compose.yml` / `.env`. Change them before deploying to any shared environment.

### Service URLs

| Service            | URL                         |
| ------------------ | --------------------------- |
| Frontend           | http://localhost:3000       |
| Backend API        | http://localhost:8001       |
| API Docs (Swagger) | http://localhost:8001/docs  |

---

## Environment Variables

Create a file named `.env` in the project root:

```env
# PostgreSQL
POSTGRES_USER=admin
POSTGRES_PASSWORD=your_password
POSTGRES_DB=meet_control

# JWT
JWT_SECRET=your_very_long_random_secret
JWT_ALGORITHM=HS256

# Super Admin (created automatically on first startup)
SUPER_ADMIN_USERNAME=admin
SUPER_ADMIN_PASSWORD=1234

# Dual CMS — Audio Server
CMS_AUDIO_URL=https://192.168.20.200:445

# Dual CMS — Video Server
CMS_VIDEO_URL=https://192.168.20.201:445

# CMS Credentials (shared for both servers)
CMS_USERNAME=admin
CMS_PASSWORD=your_cms_password

# CMS Options
CMS_API_PREFIX=/api/v1        # API path prefix on the CMS server
CMS_TIMEOUT=30
CMS_VERIFY_SSL=false          # set true if using valid TLS cert

# API behaviour
RESET_DB=0
USE_ALEMBIC=1
TZ=Asia/Jerusalem
```

> **RESET_DB=1** drops all tables and deletes all data on the next startup. Always keep it at `0` in production.

> **USE_ALEMBIC=1** runs `alembic upgrade head` automatically before `uvicorn` starts.

> **CMS_API_PREFIX** defaults to `/api/v1`. Change only if your CMS server uses a different path.

### Database migrations

The backend uses Alembic under `Backend/alembic`.

```bash
# from the Backend/ directory
alembic upgrade head
alembic revision -m "describe_change"
```

---

## CI/CD

Workflow files are under `workflows/` (copy to `.github/workflows/` for GitHub Actions):

- **`ci.yml`** — runs on every push/PR: frontend lint + build, backend Ruff lint + pytest.
- **`deploy-ubuntu.yml`** — deploys to Ubuntu on push to `main` or manual trigger.

Deploy workflow steps:

1. SSH into the Ubuntu server.
2. Pull latest `main`.
3. Copy server-side `.env.prod` → `.env`.
4. Run `docker compose -f docker-compose.prod.yml up -d --build`.

Required GitHub Secrets:

| Secret           | Description                              |
| ---------------- | ---------------------------------------- |
| `DEPLOY_HOST`    | Server IP or hostname                    |
| `DEPLOY_USER`    | SSH username                             |
| `DEPLOY_SSH_KEY` | Private SSH key                          |
| `DEPLOY_PORT`    | SSH port (optional, default `22`)        |
| `DEPLOY_PATH`    | Deploy path (optional, default `/opt/meet-control`) |

---

## Production Deployment

### Ubuntu server prerequisites

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin git
sudo systemctl enable --now docker
```

### First-time setup (standalone)

```bash
git clone <your-repo-url> /opt/meet-control
cd /opt/meet-control
cp .env.prod.example .env.prod
nano .env.prod
docker compose -f docker-compose.prod.yml up -d --build
```

### First-time setup (SSOT)

```bash
docker network create ssot-net          # if not already created
docker compose -f docker-compose-ssot.yml up -d
```

After CI/CD is configured, subsequent deployments trigger automatically on push to `main`.

---

## Roles & Permissions

The system has three roles with a strict hierarchy:

```
super_admin  >  admin  >  agent
```

### super_admin

- Full access to everything
- Can create users of all roles (admin, agent)
- Only role that can **create** new meetings
- Can update meeting passwords
- Sees all users including other super_admins
- Can delete any user (except themselves)

### admin

- Can create agent users
- Can manage groups: create, update, delete
- Can add/remove members to/from groups with an access level
- Can assign meetings to groups
- Can update and delete existing meetings
- Cannot create new meetings
- Cannot see or manage super_admin users
- Access to audio/video meetings is controlled by `can_audio` and `can_video` flags (configurable by super_admin)
- Can assign agents to any access level in a group regardless of own access flags

### agent

- Can see only the groups they belong to
- Can see only meetings whose type matches their access level in that group
- Cannot create users, meetings, or groups

---

## Admin Access Levels

Each `admin` user can be granted access to `audio` meetings, `video` meetings, or both — via the boolean flags `can_audio` and `can_video`.

| Flag | Behaviour |
|---|---|
| `can_audio = true` | Admin can see and manage audio meetings |
| `can_video = true` | Admin can see and manage video meetings |
| Both flags `true` | Admin has access to both types |
| Both flags `false` | Admin has no meeting type access |

- Configured via the Users page using checkboxes (replaces the old single `responsible_access_level` dropdown)
- Stored as two separate boolean columns on the `users` table: `can_audio`, `can_video`
- The sidebar dynamically shows `/audio-meetings` and/or `/video-meetings` links based on these flags
- Admins can assign agents to **any** access level in a group — the type restriction applies only to meeting management, not member management

> The legacy `responsible_access_level` field is kept for backwards compatibility but is no longer the primary access control mechanism.

---

## Access Level System

When an admin adds a user (agent) to a group, they must assign one of three access levels:

| Level        | Meeting type visible     |
| ------------ | ------------------------ |
| `audio`      | Audio meetings only      |
| `video`      | Video meetings only      |
| `blast_dial` | Blast dial meetings only |

This is stored in the `member_group_access` table with a composite primary key of `(member_uuid, group_uuid, access_level)`.

**Agent group restriction:** An agent can belong to **only one group**. Attempting to add an agent to a second group returns HTTP 400.

**Meeting multi-group support:** A single meeting can be assigned to **multiple groups** simultaneously. The `group_meeting` table PK is `(meeting_number, access_level, group_uuid)` — the same meeting can appear in many groups.

Meeting type identification:
- Stored explicitly in the `accessLevel` field of the meetings table
- Frontend fallback: inferred from meeting number prefix — `89xxx` = audio, `77xxx` = video, `55xxx` = blast_dial

---

## API Reference

All endpoints require a valid JWT token, which is stored in HTTP-only cookies on login. Subsequent requests send the cookies automatically.

### Auth

| Method | Endpoint        | Auth     | Description                                  |
| ------ | --------------- | -------- | -------------------------------------------- |
| POST   | `/auth/login`   | None     | Login with s_id + password, sets JWT cookies |
| GET    | `/protected/me` | Any role | Returns current user details                 |

**Login request body:**

```json
{
  "s_id": "admin",
  "password": "1234"
}
```

**Login response body:**

```json
{
  "message": "Login successful",
  "role": "super_admin",
  "s_id": "admin"
}
```

**Response cookies:** `access_token`, `refresh_token` (HTTP-only, SameSite=Lax, `Secure` controlled by `COOKIE_SECURE`).

---

### Users

| Method | Endpoint                       | Auth               | Description                                              |
| ------ | ------------------------------ | ------------------ | -------------------------------------------------------- |
| GET    | `/users/all`                   | All roles          | Get all users (super_admin sees everyone)                |
| GET    | `/users/{s_id}`                | All roles          | Get a specific user                                      |
| POST   | `/users/create-agent`          | admin, super_admin | Create an agent user                                     |
| POST   | `/users/create-admin`          | super_admin only   | Create an admin user (optionally with `responsible_access_level`) |
| PUT    | `/users/update/{user_uuid}`    | admin, super_admin | Update user details including `responsible_access_level` |
| DELETE | `/users/{user_id}`             | admin, super_admin | Delete a user                                            |
| GET    | `/users/group/{uuid}/meetings` | All roles          | Get meetings for a group by access level                 |

---

### Groups

| Method | Endpoint                                                         | Auth                                     | Description                                                             |
| ------ | ---------------------------------------------------------------- | ---------------------------------------- | ----------------------------------------------------------------------- |
| POST   | `/groups/create`                                                 | admin, super_admin                       | Create a new group                                                      |
| GET    | `/groups/all`                                                    | All roles                                | List all groups (agents see only their own)                             |
| GET    | `/groups/{group_uuid}/members`                                   | All roles                                | Get members of a group (agent only if they belong to that group) |
| GET    | `/groups/{group_uuid}`                                           | admin, super_admin                       | Get a single group                                                      |
| PUT    | `/groups/{group_uuid}`                                           | admin, super_admin                       | Update group name                                                       |
| DELETE | `/groups/{group_uuid}`                                           | admin, super_admin                       | Delete a group                                                          |
| POST   | `/groups/{group_uuid}/add-member/{user_uuid}?access_level=audio` | admin, super_admin, agent | Add user to group (admin restricted to their `responsible_access_level`) |
| POST   | `/groups/{group_uuid}/remove-member/{user_uuid}`                 | admin, super_admin        | Remove user from group                                                  |
| POST   | `/groups/{group_uuid}/add-meeting/{meeting_number}`              | admin, super_admin       | Link a meeting to a group (by meeting number)                           |
| POST   | `/groups/{group_uuid}/remove-meeting/{meeting_number}`           | admin, super_admin       | Unlink a meeting from a group (by meeting number)                       |

---

### Meetings

**Important:** All meeting operations now use the meeting number (`m_number`) as the primary identifier, not UUID. The system is CMS-First — meetings live in CMS, DB stores only overlay data.

| Method | Endpoint                                      | Auth               | Description                                                                    |
| ------ | --------------------------------------------- | ------------------ | ------------------------------------------------------------------------------ |
| GET    | `/meetings/all_meetings`                      | All roles          | Get meetings from CMS (supports `?access_level=` filter, enriched with DB overlay) |
| GET    | `/meetings/{meeting_number}`                  | All roles          | Get a single meeting by number (from CMS + DB overlay)                        |
| GET    | `/meetings/number/{number}`                   | admin, super_admin | Find meeting by number (alias for above)                                        |
| POST   | `/meetings/create_meeting`                    | super_admin only   | Create a meeting in CMS (write-through)                                        |
| DELETE | `/meetings/{meeting_number}`                  | admin, super_admin | Delete a meeting from CMS + clean DB overlay (write-through)                    |
| PUT    | `/meetings/password/{meeting_number}`          | admin, super_admin | Update meeting password in CMS (write-through)                                 |
| PUT    | `/meetings/name/{meeting_number}`             | admin, super_admin | Update meeting name in CMS — **not available for audio meetings**              |
| GET    | `/meetings/group/{group_uuid}`                | admin, super_admin | Get meeting numbers for a group (from DB)                                      |
| GET    | `/meetings/live-status`                       | admin, super_admin | Live CMS stats: active calls + participants per meeting type                   |
| GET    | `/meetings/{meeting_number}/participants`     | All roles          | Get authorized users for this meeting — returns `S_ID` + `username` per participant (from DB via group membership) |
| GET    | `/meetings/{meeting_number}/live-participants`| All roles          | Get live call participants from CMS                                            |
| POST   | `/meetings/{meeting_number}/mute`             | admin, super_admin | Mute or unmute a live participant (`call_id`, `leg_id`, `mute`)                |
| POST   | `/meetings/{meeting_number}/kick`             | admin, super_admin | Remove a live participant from a call (`call_id`, `leg_id`)                    |

> `participants` returns all users who are members of a group linked to this meeting, filtered by matching access level.  
> `blast_dial` meetings are not yet supported in CMS-First architecture.  
> All create/update/delete operations automatically sync to CMS (write-through pattern).

**Create meeting request body:**

```json
{
  "m_number": "891234",
  "name": "Meeting Name",
  "accessLevel": "audio",
  "password": "optional-password"
}
```

**Update password request body:**

```json
{
  "password": "new-password"
}
```

**Update name request body:**

```json
{
  "name": "New Meeting Name"
}
```

### Favorites

| Method | Endpoint                                | Auth      | Description                                                         |
| ------ | --------------------------------------- | --------- | ------------------------------------------------------------------- |
| GET    | `/favorites/meetings`                   | All roles | List current user's favorite meetings (with password, participants) |
| POST   | `/favorites/meetings/{meeting_number}`  | All roles | Add a visible meeting to favorites                                  |
| DELETE | `/favorites/meetings/{meeting_number}`  | All roles | Remove a meeting from favorites                                     |

### Logs

| Method | Endpoint                    | Auth        | Description                                      |
| ------ | --------------------------- | ----------- | ------------------------------------------------ |
| GET    | `/logs/dates`               | super_admin | List all available log dates (DD-MM-YYYY)        |
| GET    | `/logs/{date}/{type}`       | super_admin | Get log lines for a date by type: `info`, `warnings`, `errors` |
| GET    | `/logs/{date}/download`     | super_admin | Download a single text file combining all 3 log types for the date |
| GET    | `/logs/download-all`        | super_admin | Download a zip archive containing all log files    |

---

## Database Schema

### Tables

**users**
| Column | Type | Notes |
|---|---|---|
| UUID | UUID PK | Auto-generated |
| s_id | String UNIQUE | Login identifier |
| username | String | Display name |
| password | String | Argon2 hash |
| role | Enum | super_admin / admin / agent |
| responsible_access_level | String nullable | Legacy field, kept for compatibility |
| can_audio | Boolean | Admin can manage audio meetings |
| can_video | Boolean | Admin can manage video meetings |

**groups**
| Column | Type | Notes |
|---|---|---|
| UUID | UUID PK | Auto-generated |
| name | String UNIQUE | Group name |

**member_group_access**  
Composite primary key `(member_uuid, group_uuid, access_level)` — controls what a user can see in a specific group.

**user_group_association**  
Many-to-many join table between users and groups.

**group_meeting** (many-to-many: meetings ↔ groups)
| Column | Type | Notes |
|---|---|---|
| group_uuid | UUID FK | Group UUID |
| meeting_number | String | Meeting number (from CMS) |
| access_level | String | audio / video - matches meeting type |
| Composite PK | (meeting_number, access_level, group_uuid) | One meeting can belong to multiple groups |

**favorite_meeting** (updated - now uses meeting_number)
| Column | Type | Notes |
|---|---|---|
| user_uuid | UUID FK | User UUID |
| meeting_number | String | Meeting number (from CMS) |
| access_level | String | audio / video - matches meeting type |
| created_at | Timestamp | When favorited |
| Composite PK | (user_uuid, meeting_number, access_level) | |

### Relationships

```
User ——< user_group_association >—— Group
User ——< member_group_access >————  Group (with access_level)
Group —< group_meeting >——————— Meeting (by meeting_number + access_level)
User ——< favorite_meeting >————— Meeting (by meeting_number + access_level)
```

### Key Changes from Previous Architecture

- **Removed `meetings` table** — meeting data now lives in CMS only
- **Removed `meeting_group_association`** — replaced by `group_meeting` with meeting_number
- **Removed `meeting_participant_status`** — live participant tracking now done via CMS
- **Updated `favorite_meeting`** — now uses meeting_number instead of UUID
- **Added `group_meeting`** — stores meeting-to-group associations by meeting_number and access_level

---

## Frontend Pages

| Path                   | Page                | Who can access                   | Features                                                                                            |
| ---------------------- | ------------------- | -------------------------------- | --------------------------------------------------------------------------------------------------- |
| `/login`               | Login               | Everyone (unauthenticated)       | Basic authentication                                                                                |
| `/dashboard`           | Dashboard           | admin, super_admin               | Live meeting stats (active calls + participants by type), favorite meetings panel with full actions: edit name, edit password, delete, participants, assign group, remove favorite |
| `/users`               | User management     | All roles                        | Create users (admin creates agents; super_admin creates admins+agents), edit user details, `can_audio`/`can_video` checkboxes for admin users, delete users, search & filter |
| `/groups`              | Group management    | All roles                        | Create/edit/delete groups, manage members with access levels (audio/video/blast_dial), assign multiple meetings per group, agent one-group rule enforced |
| `/audio-meetings`      | Audio meetings      | Agents with audio access, admins with `can_audio=true`    | Browse audio meetings, search by meeting number / group name / no-group filter, authorized participant count per meeting, assign multiple groups from card (admin+), pagination, participants modal (authorized + live tabs) |
| `/video-meetings`      | Video meetings      | Agents with video access, admins with `can_video=true`    | Browse video meetings, search by meeting number / group name / no-group filter, authorized participant count, assign multiple groups from card (admin+), pagination, create meeting (super_admin), participants modal (authorized + live tabs) |
| `/blast-dial-meetings` | Blast dial meetings | Users with blast_dial access     | Browse blast dial meetings, search by meeting number / group name / no-group filter, authorized participant count, assign group from card (admin+), pagination, create meeting (super_admin), participants modal with tabs |
| `/reports`             | Reports             | admin, super_admin               | Participant report (דוח משתתפים) + unused meetings report                                           |
| `/servers`             | Servers             | super_admin only                 | Manage CMS servers: audio/video/blast-dial types with IP, username, password                        |
| `/logs`                | Logs                | super_admin only                 | Accordion log viewer — per date, 3 tabs, lazy-loaded, newest first, download per date or all logs |
| `/profile`             | Profile             | All roles                        | Current user info                                                                                   |
| `/help`                | Help                | All roles                        | Guidance & documentation                                                                            |

Routes are guarded by `ProtectedRoute` — any unauthenticated access redirects to `/login`.

The sidebar dynamically shows/hides `/audio-meetings` and `/video-meetings` links based on the current user's `can_audio` / `can_video` flags (for admins) or group memberships (for agents).

---

## Meeting Card Features

Each meeting card on the Audio / Video / Blast-dial pages displays:

- **Meeting number** — e.g. `Meeting #770`
- **UUID** — visible to `admin` and `super_admin` only
- **Groups + Participant count** — all assigned group names (pipe-separated) + number of authorized participants (from DB)
- **Password** — shown if set
- **Action buttons** (role-dependent):
  - ★ Favorite / Unfavorite
  - ✏ Edit name (`admin`, `super_admin`) — **not available for audio meetings**
  - ✏ Edit password (`admin`, `super_admin`)
  - 🗑 Delete (`admin`, `super_admin`)
  - 👥 View participants (all roles)
  - 📁 Assign group (`admin`, `super_admin`)
  - Access level badge (Audio 🎧 / Video 📹 / Blast-dial 🚀)

### Search & Filter

The search bar supports four modes via dropdown:

| Mode | Behaviour |
|---|---|
| All | Shows all meetings immediately (no input required) |
| Name or Number | Prefix (`startsWith`) search by meeting name or number — shows nothing until typing |
| Group | Prefix search by resolved group name — shows nothing until typing |
| No Group | Filter to show only unassigned meetings |

### Pagination

Results are paginated — 10 per page, with ← → navigation displayed when there are more than 10 meetings.

### Assign Group Modal

Opened via 📁 button. Allows:
- Selecting a group from a dropdown and adding it to the meeting (additive — does not replace)
- Viewing all currently assigned groups for the meeting
- Removing any individual group assignment via a per-group Remove button
- A meeting can be assigned to **multiple groups** simultaneously

### Toast Notifications

A brief overlay message appears at the bottom of the screen (3 seconds) after:
- Group assigned / removed
- Password updated
- Name updated
- Meeting added / removed from favorites

### Participant Count

The `participant_count` field is calculated in the backend `MeetingService._to_output` method by iterating over the meeting's groups and counting unique members whose `access_level` matches the meeting's `accessLevel`. This count is included in every `MeetingOutput` response.

### Dashboard — Group Meeting Counts

The Group Activity Snapshot counts are derived from `GET /meetings/all_meetings` — which returns only meetings the current user is authorized to see — rather than from the raw group relationship. This ensures `agent` roles, and `admin` roles with `responsible_access_level`, see accurate counts based on their permissions.

---

## Authentication Flow

```
1. User submits s_id + password on /login
2. Frontend calls POST /auth/login
3. Backend verifies password against Argon2 hash in DB
4. Backend signs access + refresh JWTs and sets them as HTTP-only cookies
5. AuthContext calls GET /protected/me to fetch full user object
6. All subsequent API calls send the cookies automatically
7. TokenValidator (FastAPI dependency) decodes JWT + verifies user exists in DB
8. On logout: cookies are cleared, AuthContext state is cleared
9. On page reload: AuthContext re-checks the session via /protected/me
```

If the token is invalid or expired, all protected endpoints return `401`.

---

## Logging System

All significant actions (create, delete, update, errors) are recorded by `LoggerManager` in `logger.py`.

Each day produces a dedicated directory with **three separate log files**:

```
logs/
└── DD-MM-YYYY/
    ├── info.log      ← INFO level (regular operations)
    ├── warnings.log  ← WARNING level
    └── errors.log    ← ERROR + CRITICAL
```

- Log writes go through a dedicated async queue (`QueueListener`) — no HTTP request blocking
- Each file auto-rotates by size (default 10 MB, configurable `backup_count`)
- Old log directories are **deleted after retention period** (default 7 days, configurable via `retention_days` in `main.py`)
- `LevelFilter` per handler ensures strict separation between levels
- Timestamps use `Asia/Jerusalem` timezone
- Initialized once in `main.py` via `LoggerManager.initialize()`
- Logs volume is mounted: `./Backend/logs:/app/logs`

### Log Viewer (frontend `/logs`)

- Accessible to `super_admin` only (sidebar link + route guard)
- Lists all available log dates as expandable accordions
- Each accordion contains **3 tabs**: פעולות (Info) · אזהרות (Warnings) · שגיאות (Errors)
- Tab content is **lazy-loaded** — only fetched on first click, then cached
- Lines are displayed in **reverse order** (newest at top)
- Download options:
  - **Download** button per date — returns a single text file combining all 3 log types
  - **Download all logs** button — returns a zip archive of all log date folders

**Example log lines:**

```
[INFO]-17:15:23 Creating viewer user with s_id=logviewer001 by requester s_id=superadmin role=super_admin
[INFO]-17:15:23 AUDIT mutation POST /users/create-viewer | query=- | user=superadmin:super_admin ip=172.18.0.1 | status=200 | duration_ms=151.18
```

---

## Security

- **Passwords** hashed with Argon2 (one of the strongest available algorithms)
- **JWT** signed with HS256 and a configurable secret — tokens expire after 24 hours
- **Role enforcement** at every endpoint via `TokenValidator` FastAPI dependency
- **No sensitive data** returned in API responses (passwords never exposed)
- **CORS** configured in `main.py` to allow only the frontend origin
- **RESET_DB=0** must be kept in `.env` to protect production data

---

## CMS Integration

### Backend CMS Service (`Backend/app/service/cms.py`)

A dedicated `CMS` class connects directly to the Cisco Meeting Server via HTTP Basic Auth + the `/api/v1` REST API.

**Instantiation:**
```python
cms = CMS(cms_type="audio")   # connects to CMS_AUDIO_URL
cms = CMS(cms_type="video")   # connects to CMS_VIDEO_URL
```

**Available methods:**

| Method | Description |
|--------|-------------|
| `create_cospace(name, uri, passcode)` | Create a new CoSpace (meeting room) |
| `delete_cospace(cospace_id)` | Delete a CoSpace by internal CMS ID |
| `delete_cospace_by_call_id(call_id)` | Delete a CoSpace by Call ID |
| `list_cospaces()` | List all CoSpaces on the server |
| `get_cospace_details(cospace_id)` | Get details of a specific CoSpace |
| `get_cospace_by_call_id(call_id)` | Find a CoSpace by its Call ID |
| `update_cospace_passcode(cospace_id, passcode)` | Update CoSpace passcode by internal ID |
| `update_cospace_passcode_by_call_id(call_id, passcode)` | Update CoSpace passcode by Call ID |
| `update_cospace_name(cospace_id, name)` | Update CoSpace name by internal ID |
| `update_cospace_name_by_call_id(call_id, name)` | Update CoSpace name by Call ID |
| `get_active_calls()` | Get all active calls currently running |
| `get_call_details(call_id)` | Get details of a specific call |
| `get_call_participants(call_id)` | Get participants in a call |
| `mute_participant_by_leg_id(call_id, leg_id, mute)` | Mute/unmute a participant |
| `kick_participant_by_leg_id(call_id, leg_id)` | Remove a participant from a call |
| `test_connection()` | Returns `True` if CMS is reachable |
| `get_system_info()` | Returns CMS system info |

**SSL:** verification disabled by default (self-signed cert environment). Set `CMS_VERIFY_SSL=true` if using a valid certificate.

> The `participants` endpoint in the Meetings API uses the DB (group memberships), not the CMS live call state.

---

## Dual CMS Architecture

The system connects to **two separate CMS servers** — one for audio meetings, one for video meetings.

### Routing logic

| Meeting type | CMS server used      | Env variable    |
|-------------|----------------------|-----------------|
| `audio`     | Audio CMS            | `CMS_AUDIO_URL` |
| `video`     | Video CMS            | `CMS_VIDEO_URL` |
| `blast_dial`| **Not supported** — excluded from all CMS calls | — |

### CMS-First data flow

**Read operations:**
```
1. Frontend requests meetings (e.g., GET /meetings/all_meetings)
2. Backend queries CMS for CoSpaces (audio + video servers)
3. Backend enriches with DB overlay data (groups, favorites, participant counts)
4. Frontend displays enriched meeting data
```

**Write operations (create/update/delete):**
```
1. Frontend sends request to backend
2. Backend performs operation on CMS (write-through)
3. Backend updates DB overlay if needed (group associations, favorites)
4. Response includes updated data from CMS
```

### Create meeting flow

When a super_admin creates a meeting via the UI:

```
1. POST /meetings/create_meeting → creates CoSpace on CMS
2. Backend validates meeting number doesn't already exist
3. CMS returns created CoSpace details
4. Meeting data is returned from CMS (no DB storage of meeting data)
```

### Update password flow

When a user updates a meeting password:

```
1. PUT /meetings/password/{meeting_number} → updates passcode on CMS
2. Backend finds CoSpace by meeting number
3. CMS updates the passcode
4. Updated CoSpace data is returned
```

### Delete meeting flow

When an admin deletes a meeting:

```
1. DELETE /meetings/{meeting_number} → deletes CoSpace from CMS
2. Backend removes CoSpace from CMS
3. Backend cleans up DB overlay (group associations, favorites)
4. Success response returned
```

### API prefix

The CMS REST API is served under `/api/v1` (not the root path). This is configured via `CMS_API_PREFIX` (default: `/api/v1`). The `CMS` class appends this automatically to the base URL.

```
https://192.168.20.200:445/api/v1/coSpaces  ← correct
https://192.168.20.200:445/coSpaces         ← returns 404
```

### CMS API format

The CMS service now uses **form data** instead of XML for create/update operations:

```python
# Create CoSpace
form_data = {"name": name, "uri": uri, "passcode": passcode}
response = session.post(url, data=form_data)

# Update passcode
form_data = {"passcode": passcode}
response = session.put(url, data=form_data)
```

This change was made because the CMS API was not accepting XML payloads correctly, returning empty responses.

---

## Recent Changes

### Meeting Identifier: URI → Call ID

- The system now uses **Call ID** (`callId`) as the primary meeting identifier instead of URI user part
- `MeetingService._to_output` — `m_number` now read from `cs.get("callId")` instead of `cs.get("uri")`
- `get_all_meetings` — filters CoSpaces by `callId` field
- `_find_cospace`, `_find_cospace_by_type` — look up CoSpaces via `get_cospace_by_call_id`
- `cms.py` — added new `*_by_call_id` methods: `get_cospace_by_call_id`, `delete_cospace_by_call_id`, `update_cospace_passcode_by_call_id`, `update_cospace_name_by_call_id`
- Old `*_by_uri` methods retained as legacy (used internally only)

### Edit Meeting Name Feature

- New `PUT /meetings/name/{meeting_number}` endpoint — updates meeting name directly on CMS
- New `MeetingNameUpdate` Pydantic schema (`Backend/app/schema/meeting.py`)
- `MeetingService.update_name_by_number` — access-controlled name update with CMS sync
- `cms.update_cospace_name` / `update_cospace_name_by_call_id` — CMS API integration
- **Frontend — Meetings pages:** "Edit Name" button added to each meeting card (admin, super_admin only)
  - **Audio meetings: edit name disabled** (not applicable for audio CoSpaces)
  - Inline input row with save/cancel and error display
  - Clears password edit state when opened (and vice versa)
- **Frontend — Dashboard favorites:** same Edit Name capability added to the favorites panel
- `api.js` — added `meetingAPI.updateMeetingName(meetingNumber, newName, accessLevel)`

### Meeting Search Enhancements

- Added **"All" option** to search dropdown — shows all meetings immediately with no input required
- Other search modes (Name/Number, Group) show **no results until typing** begins
- All search filters changed from `includes` to **`startsWith`** (prefix matching only)
- Search input hidden when "All" or "No Group" is selected

### Dashboard Favorites — Full Action Parity

- Favorites panel now supports all the same actions as the Meetings pages:
  - Edit Name (admin+, video/blast_dial only)
  - Edit Password (admin+)
  - Delete meeting
  - View participants (authorized + live tabs)
  - Assign / remove group
- Fixed: all favorites API calls now use `m_number` (previously erroneously used `meeting_uuid` which was `undefined`)

### Groups Page — Meeting Search & Filter Enhancements

- Added **type filter dropdown** (All / Audio / Video / Blast Dial) above the meeting search input in the Add Meetings section
- Meeting search now searches by **number, name, and type** (previously number only)
- Meeting list items now display `#number — Name (type)` format
- Assigned meetings table now includes a **Name column**
- Type filter resets to "All" when opening a new group modal

### Groups Page — Member Search Enhancements

- Added **role filter dropdown** (All roles / Agent / Admin) above the member search input in the Add Member section
- Member search upgraded from `startsWith` to `includes` for broader matching
- Role filter resets when opening a new group modal

### Groups Page — Code Refactor

- `Groups.jsx` (~1,300 lines) split into three focused files:
  - `Groups.jsx` (~500 lines) — orchestrator: group list, create/edit/delete, modal open/close
  - `GroupMembersPanel.jsx` — all member management logic and UI (add, remove, access levels, role filter)
  - `GroupMeetingsPanel.jsx` — all meeting assignment logic and UI (add, remove, type filter, name search)
- No functional changes — pure structural refactor

### Dashboard — "Unknown" Category Removed

- Meetings with an unrecognized `accessLevel` are now silently skipped in live stats (no longer shown as "unknown")
- `LiveActivityChart.jsx` — removed "unknown" from chart labels and data
- `Dashboard.jsx` — `meetings.forEach` now skips non-audio/video/blast_dial meetings

### CMS XML Encoding Fix (Hebrew Support)

- All `ET.fromstring(response.text)` calls replaced with `ET.fromstring(response.content)` in `cms.py`
- Fixes Hebrew meeting names displaying as garbled characters — Python now reads encoding from the XML declaration instead of guessing

### Multi-Group Meeting Support

- A meeting can now be assigned to **multiple groups** simultaneously
- The `group_meeting` table PK already supported this — only the enforcement layer was removed
- `groupRepo.add_meeting_to_group_by_number` — removed the block that prevented assigning a meeting already linked to another group
- `MeetingsPage.jsx` — Assign Group modal updated: now shows all assigned groups with per-group Remove button; Add button is additive (no longer replaces)
- `meeting.group` (single UUID) replaced with `meeting.groups` (array) throughout `AudioMeetings.jsx`, `VideoMeetings.jsx`, `MeetingsPage.jsx`
- Group search and sort updated to work across multiple groups per meeting

### Admin Multi-Access Level (can_audio / can_video)

- Replaced the single `responsible_access_level` field with two boolean flags: `can_audio`, `can_video`
- DB migration: `ALTER TABLE users ADD COLUMN can_audio BOOLEAN NOT NULL DEFAULT FALSE; ADD COLUMN can_video BOOLEAN NOT NULL DEFAULT FALSE;`
- `UserOutput` and `UserLoginOutput` schemas updated to include both flags
- Login response now includes `can_audio` and `can_video`
- `AuthContext.normalizeUser` stores both flags; sidebar uses them to show/hide meeting type links
- `Users.jsx` — admin creation/edit forms now show two checkboxes instead of a dropdown
- `meetingService._assert_admin_access` and `get_all_meetings` use `can_audio`/`can_video`
- `groupService` access control updated to use the new flags

### Agent One-Group Rule

- An agent can now belong to **only one group**
- Enforced in `groupRepo.add_member_to_group`: if the agent already has a `MemberGroupAccess` in a different group, HTTP 400 is raised
- Admin can assign agents to **any access level** (audio/video/blast_dial) regardless of the admin's own `can_audio`/`can_video` flags

### Participant S_ID Display

- `GET /meetings/{meeting_number}/participants` now returns `S_ID` (login identifier) as a separate field
- `MeetingsPage.jsx` participant table header and data updated to show `S_ID` instead of `name`

---

## Recent Changes (July 1, 2026)

### Major Architecture Migration: CMS-First

The system was migrated from a DB-first architecture to a **CMS-First architecture**. This is a significant change that affects how meetings are stored and managed.

**Key changes:**

1. **Meetings now live in CMS only**
   - Removed the `meetings` table from the database
   - CoSpaces in Cisco Meeting Server are now the single source of truth
   - Database serves as overlay for permissions, groups, and favorites only

2. **Meeting identification changed from UUID to meeting number**
   - All API endpoints now use `m_number` (meeting number) instead of UUID
   - Updated all meeting-related endpoints to use `/meetings/{meeting_number}` pattern
   - Frontend updated to use meeting numbers for all operations

3. **Database schema changes**
   - Removed: `meetings` table, `meeting_group_association` table, `meeting_participant_status` table
   - Added: `group_meeting` table (stores meeting_number + access_level)
   - Updated: `favorite_meeting` table (now uses meeting_number instead of UUID)

4. **API endpoint changes**
   - Removed: `/meetings/{uuid}/cms-create`, `/meetings/{uuid}/cms-delete`, `/meetings/{uuid}/cms-password`, `/meetings/{uuid}/cms-sync`, `/meetings/cms-import`
   - Added: `/meetings/{meeting_number}` (get single meeting), `/meetings/password/{meeting_number}` (update password)
   - Updated: All meeting endpoints now use meeting_number as identifier
   - Write-through pattern: create/update/delete operations automatically sync to CMS

5. **CMS integration changes**
   - Changed from XML to form data for CMS API calls
   - CMS service now uses `session.post(url, data=form_data)` instead of XML payloads
   - This was necessary because CMS was not accepting XML payloads correctly

6. **Frontend changes**
   - Removed separate CMS create/sync/delete buttons (now automatic via write-through)
   - Updated search to use `startsWith` for name search (prefix matching only)
   - Removed CMS-specific API calls from frontend service
   - All meeting operations now go through the main backend endpoints

7. **Removed code**
   - `Backend/app/repository/meetingRepo.py` - no longer needed
   - `Backend/app/models/meeting_participant_status.py` - no longer needed
   - Frontend CMS-specific handlers and state variables

8. **Database constraints updated**
   - `m_number` field increased from `VARCHAR(15)` to `VARCHAR(50)` to support longer meeting numbers
   - `password` field increased to `VARCHAR(120)` to support longer passwords

### Migration Notes

If you have existing data in the old architecture:

1. **Backup your database** before migration
2. **Export existing meetings** from the `meetings` table
3. **Import meetings to CMS** using the CMS API or admin interface
4. **Update group associations** to use meeting numbers instead of UUIDs
5. **Update favorites** to use meeting numbers instead of UUIDs

The new architecture is simpler and more aligned with the actual data source (CMS), but requires careful migration of existing data.

---

## Recent Changes (July 12, 2026)

### CMSFactory — Connection Caching & Fault Tolerance

`Backend/app/service/cms.py` — `CMSFactory` was refactored to improve performance and resilience:

- **Active-server cache (`CACHE_TTL = 30s`):** Once a CMS server is verified reachable, it is reused for 30 seconds without re-checking. Eliminates a 3-second `check_connection` call on every API request.
- **Dead-server cooldown (`DEAD_TTL = 120s`):** A server that fails `check_connection` is marked "dead" and skipped for 2 minutes. After the cooldown, it is retried automatically — no restart required.
- **Automatic failover:** If the primary server (priority=1) is unreachable, the factory moves to the next server in priority order (priority=2, etc.) within the same CMS type.
- **Cache invalidation:** `CMSFactory.invalidate()` is called automatically from `server.py` whenever a server is created, updated, or deleted — ensuring the cache never holds a stale server reference.

### CMS Server Prioritization per Meeting Type

`Backend/app/service/meetingService.py` — `_find_cospace` now accepts an `access_level` hint:

- When `hint="video"` is passed, the factory tries the video CMS first instead of iterating all types
- `delete_meeting`, `update_name_by_number`, `update_password_by_number` all propagate the hint
- The `DELETE /meetings/{meeting_number}` endpoint accepts an optional `?access_level=` query param and passes it as the hint
- Frontend (`MeetingsPage.jsx`, `Dashboard.jsx`) sends `accessLevel` in all delete calls

### Favorites — Bug Fixes

- **`favoriteMeetingService._to_output`:** changed from `get_cospace_by_uri(number)` to `get_cospace_by_call_id(number)` — favorites were silently dropped because `meeting_number` stores the `callId`, not the URI
- **Dashboard auto-refresh:** favorites panel now reloads together with live stats (every 30 seconds) and also on `visibilitychange` (when user returns to the Dashboard tab from another page)

### CMS Create CoSpace — `callId` Field Added

`Backend/app/service/cms.py` — `create_cospace` now sends `callId=uri` in the form payload alongside `uri`. Meetings created without a `callId` were invisible in all meeting list views because `get_all_meetings` filters by `callId`.

### Route Conflict Fix

`Backend/app/routers/user.py` — `/uuid/{uuid}` route moved before `/{s_id}` to prevent FastAPI from matching UUID paths as s_id values.

### Nginx API Proxy

`Frontend/nginx.conf` — added `proxy_pass` blocks for all API route prefixes (`/auth`, `/users`, `/groups`, `/meetings`, `/protected`, `/favorites`, `/servers`, `/logs`, `/reports`). Without this, all API calls returned 404 in production.

### CORS — Dynamic Origins from Environment Variable

`Backend/main.py` — CORS `allow_origins` now reads from the `CORS_ORIGINS` environment variable (comma-separated, single line). Falls back to a hardcoded dev list if the variable is not set.

### User Service — 404 Instead of 500

`Backend/app/service/userService.py` — `get_user_by_s_id` and `get_user_by_uuid` now raise `HTTPException(404)` when a user is not found, instead of `400`. This prevents the router's generic exception handler from returning a misleading `500`.

### Dashboard — Parallel Per-Type Requests

`Frontend/src/pages/Dashboard.jsx` — `loadLiveStats` now fires three parallel `getAllMeetings` calls (audio, video, blast_dial) using `Promise.allSettled` instead of a single unfiltered call. An unreachable CMS type no longer blocks the entire dashboard load.

---

## Data Persistence & Backups

PostgreSQL data is stored in the Docker named volume `meet-data` (standalone stack):

```yaml
volumes:
  meet-data:
```

- `docker compose down` does **not** delete data
- `docker compose down -v` **will delete** the database volume
- Data is also lost if `RESET_DB=1` is set when the API starts — keep it at `0` in production

DB snapshots can be shared via `initdb/01_restore.sql`, which is auto-loaded on first DB initialization.

**Create / update the snapshot:**

```bash
docker compose exec -T db sh -lc 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > initdb/01_restore.sql
```

**Fresh restore on another machine:**

```bash
docker compose down -v
docker compose up --build
```

**Manual restore into a running DB:**

```bash
docker compose exec -T db sh -lc 'psql -U "$POSTGRES_USER" "$POSTGRES_DB"' < initdb/01_restore.sql
```

---

## License

This project is open source and available under the MIT License.
