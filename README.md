# Meet Manager

**Meet Manager** הוא מערכת ניהול ועידות פנים-ארגונית מבוססת הרשאות תפקיד.  
המערכת מאפשרת לאדמינים לנהל מדורים, משתמשים וחדרי ועידה וירטואליים — עם בקרת גישה מפורטת ברמת המדור.

המערכת מבוססת על **CMS-First Architecture** — הפגישות חיות אך ורק בשרתי Cisco Meeting Server (CMS), וה-DB משמש כ-overlay לנתוני הרשאות, מדורים, ומועדפים. הבקאנד מתחבר לשני שרתי CMS — אחד ל-Audio ואחד ל-Video — לצורך יצירת CoSpaces, ניהול סיסמאות, ומעקב אחר שיחות חיות.

---

## Table of Contents

1. [Tech Stack](#tech-stack)
2. [Architecture](#architecture)
3. [Project Structure](#project-structure)
4. [Getting Started](#getting-started)
5. [Environment Variables](#environment-variables)
6. [CI/CD](#cicd)
7. [Production Deployment](#production-deployment)
8. [Roles & Permissions](#roles--permissions)
9. [Admin Responsible Access Level](#admin-responsible-access-level)
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
- Census API reachable at the configured `CENSUS_HOST:CENSUS_PORT`

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
- If assigned a `responsible_access_level` (audio/video) — sees and manages **only** meetings of that type

### agent

- Can see only the groups they belong to
- Can see only meetings whose type matches their access level in that group
- Cannot create users, meetings, or groups

---

## Admin Responsible Access Level

Each `admin` user can optionally be assigned a `responsible_access_level` of `audio` or `video`.

| Restriction | Behaviour |
|---|---|
| Meetings visible | Only meetings of the matching type |
| Meetings assignable to groups | Only meetings of the matching type |
| Members addable to groups | Only with matching access level |
| Members removable from groups | Only with matching access level |

If `responsible_access_level` is not set, the admin has full access with no type restriction.

Set via the Users page when creating or editing an admin user.

---

## Access Level System

When an admin adds a user (agent) to a group, they must assign one of four access levels:

| Level        | Meeting type visible     |
| ------------ | ------------------------ |
| `audio`      | Audio meetings only      |
| `video`      | Video meetings only      |
| `blast_dial` | Blast dial meetings only |
| `voice`      | Voice-only access        |

This is stored in the `member_group_access` table with a composite primary key of `(member_uuid, group_uuid, access_level)`.

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
| PUT    | `/meetings/password/{meeting_number}`          | All roles          | Update meeting password in CMS (write-through)                                 |
| GET    | `/meetings/group/{group_uuid}`                | admin, super_admin | Get meeting numbers for a group (from DB)                                      |
| GET    | `/meetings/live-status`                       | admin, super_admin | Live CMS stats: active calls + participants per meeting type                   |
| GET    | `/meetings/{meeting_number}/participants`     | All roles          | Get authorized users for this meeting (from DB via group membership)           |
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
| responsible_access_level | String nullable | audio / video — restricts admin to that meeting type only |

**groups**
| Column | Type | Notes |
|---|---|---|
| UUID | UUID PK | Auto-generated |
| name | String UNIQUE | Group name |

**member_group_access**  
Composite primary key `(member_uuid, group_uuid, access_level)` — controls what a user can see in a specific group.

**user_group_association**  
Many-to-many join table between users and groups.

**group_meeting** (new - replaces meeting_group_association)
| Column | Type | Notes |
|---|---|---|
| group_uuid | UUID FK | Group UUID |
| meeting_number | String | Meeting number (from CMS) |
| access_level | String | audio / video - matches meeting type |
| Composite PK | (group_uuid, meeting_number, access_level) | |

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
| `/dashboard`           | Dashboard           | admin, super_admin               | Live meeting stats (active calls + participants by type), group activity snapshot with accurate per-group meeting counts (filtered by user permissions), favorite meetings |
| `/users`               | User management     | All roles                        | Create users, edit user details (admin/super_admin), delete users, search & filter                  |
| `/groups`              | Group management    | All roles                        | Create/edit groups, manage members, add meetings                                                    |
| `/audio-meetings`      | Audio meetings      | Users with audio access level    | Browse audio meetings, search by meeting number / group name / no-group filter, authorized participant count per meeting, assign group from card (admin+), pagination, create disabled for audio type |
| `/video-meetings`      | Video meetings      | Users with video access level    | Browse video meetings, search by meeting number / group name / no-group filter, authorized participant count, assign group from card (admin+), pagination, create meeting (super_admin), participants modal with tabs |
| `/blast-dial-meetings` | Blast dial meetings | Users with blast_dial access     | Browse blast dial meetings, search by meeting number / group name / no-group filter, authorized participant count, assign group from card (admin+), pagination, create meeting (super_admin), participants modal with tabs |
| `/reports`             | Reports             | admin, super_admin               | Participant report (דוח משתתפים) + unused meetings report                                           |
| `/servers`             | Servers             | super_admin only                 | Manage CMS servers: audio/video/blast-dial types with IP, username, password                        |
| `/logs`                | Logs                | super_admin only                 | Accordion log viewer — per date, 3 tabs, lazy-loaded, newest first, download per date or all logs |
| `/profile`             | Profile             | All roles                        | Current user info                                                                                   |
| `/help`                | Help                | All roles                        | Guidance & documentation                                                                            |

Routes are guarded by `ProtectedRoute` — any unauthenticated access redirects to `/login`.

The sidebar dynamically shows/hides meeting type links based on the current user's access levels, fetched on login from their group memberships.

---

## Meeting Card Features

Each meeting card on the Audio / Video / Blast-dial pages displays:

- **Meeting number** — e.g. `Meeting #770`
- **UUID** — visible to `admin` and `super_admin` only
- **Group + Participant count** — resolved group name + number of authorized participants (from DB)
- **Password** — shown if set
- **Action buttons** (role-dependent):
  - ★ Favorite / Unfavorite
  - ✏ Edit password (`agent`, `admin`, `super_admin`)
  - 🗑 Delete (`admin`, `super_admin`)
  - 👥 View participants (all roles)
  - 📁 Assign group (`admin`, `super_admin`)
  - Access level badge (Audio 🎧 / Video 📹 / Blast-dial 🚀)

### Search & Filter

The search bar supports three modes via dropdown:

| Mode | Behaviour |
|---|---|
| Meeting Number | Free-text search by meeting number |
| Group | Free-text search by resolved group name |
| No Group | Filter to show only unassigned meetings |

### Pagination

Results are paginated — 10 per page, with ← → navigation displayed when there are more than 10 meetings.

### Assign Group Modal

Opened via 📁 button. Allows:
- Selecting a group from a dropdown of all existing groups
- Assigning a new group (replaces existing)
- Removing the current group assignment (with confirmation step)

### Toast Notifications

A brief overlay message appears at the bottom of the screen (3 seconds) after:
- Group assigned / removed
- Password updated
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
| `delete_cospace(cospace_id)` | Delete a CoSpace |
| `list_cospaces()` | List all CoSpaces on the server |
| `get_cospace_details(cospace_id)` | Get details of a specific CoSpace |
| `update_cospace_passcode(cospace_id, passcode)` | Update CoSpace passcode |
| `get_active_calls()` | Get all active calls currently running |
| `get_call_details(call_id)` | Get details of a specific call |
| `get_call_participants(call_id)` | Get participants in a call |
| `get_participants_by_meeting_number(m_number)` | Get participants by meeting number |
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
