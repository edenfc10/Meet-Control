# Meet Manager

**Meet Manager** is a full-stack, role-based meetings management platform built for internal organizational use.  
It enables admins to manage groups, users, and virtual meeting rooms — with fine-grained per-user access control at the group level.

The backend connects to a **Census** service (CMS) for meeting data, and maintains its own PostgreSQL database for users, groups, and access control.

---

## Table of Contents

1. [Overview](#overview)
2. [Tech Stack](#tech-stack)
3. [Architecture](#architecture)
4. [Project Structure](#project-structure)
5. [Getting Started](#getting-started)
6. [Environment Variables](#environment-variables)
7. [CI/CD](#cicd)
8. [Production Deployment](#production-deployment)
9. [Roles & Permissions](#roles--permissions)
10. [Access Level System](#access-level-system)
11. [API Reference](#api-reference)
12. [Database Schema](#database-schema)
13. [Frontend Pages](#frontend-pages)
14. [Authentication Flow](#authentication-flow)
15. [Logging System](#logging-system)
16. [Security](#security)
17. [CMS Integration](#cms-integration)
18. [Data Persistence & Backups](#data-persistence--backups)

---

## Overview

Meet Manager solves the problem of controlling who can see what type of meeting within an organization. The system supports three meeting types (audio, video, blast-dial) and assigns per-user access levels within each group. A super admin manages everything, admins manage their groups and users, agents and viewers consume meeting data according to their assigned access.

---

## Tech Stack

| Layer            | Technology                                    |
| ---------------- | --------------------------------------------- |
| Frontend         | React 19, Vite 7, React Router 7, Axios 1.6   |
| Backend          | FastAPI 0.135, SQLAlchemy, Pydantic v2        |
| Database         | PostgreSQL 15                                 |
| Auth             | JWT (PyJWT, HS256, 24h expiry)                |
| Passwords        | Argon2 (via passlib)                          |
| Containerization | Docker + Docker Compose + Nginx               |
| Logging          | Custom async queue-based rotating file logger |
| CI/CD            | GitHub Actions                                |

---

## Architecture

```
Development
Browser (React/Vite :5173)
  │
  │  HTTP + JWT Bearer token
  ▼
FastAPI Backend (:8000)
  │
  ├── SQLAlchemy ORM ──► PostgreSQL (:5432)  [users / groups / access control]
  │
  └── HTTP ────────────► Census API (:8001)  [meeting data / CMS]

Production (standalone stack)
Browser
  │
  │  HTTP
  ▼
Nginx :5173  (serves React build + reverse proxy)
  │
  ├── /              -> React static build
  └── /auth|users|groups|meetings|protected|favorites|servers -> FastAPI :8000
          │
          ├── meet-db (PostgreSQL, internal Docker network)
          └── Census API (external, configured via CENSUS_HOST/PORT)

Production (SSOT stack — docker-compose-ssot.yml)
Browser
  │
  ▼
Nginx :5173
  │
  └── meet-control-api :8000
          │
          ├── census-db (PostgreSQL on ssot-net, shared with Census)
          └── Census API (on ssot-net)
```

In **development**, the Vite dev server runs on `:5173` and the backend is accessible on `:8000`.

In the **standalone production stack** (`docker-compose.yml`), Meet has its own `meet-db` container and talks to an external Census API by IP.

In the **SSOT production stack** (`docker-compose-ssot.yml`), Meet joins the shared `ssot-net` Docker network and connects directly to `census-db`, with no local DB container.

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

| Service            | URL                        |
| ------------------ | -------------------------- |
| Frontend           | http://localhost:5173      |
| Backend API        | http://localhost:8000      |
| API Docs (Swagger) | http://localhost:8000/docs |

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
| s_id     | `superadmin`         |
| Password | `superadminpassword` |

> Change these credentials in `.env` before deploying to any shared environment.

---

## Environment Variables

Create a file named `.env` in the project root (or use `.env.prod` for production):

```env
# PostgreSQL (Meet's own database)
POSTGRES_USER=admin
POSTGRES_PASSWORD=your_password
POSTGRES_DB=meet_control

# JWT
JWT_SECRET=your_very_long_random_secret
JWT_ALGORITHM=HS256

# Super Admin (created automatically on first startup)
SUPER_ADMIN_USERNAME=superadmin
SUPER_ADMIN_PASSWORD=superadminpassword

# Census API connection
CENSUS_HOST=192.168.1.30
CENSUS_PORT=8001
CENSUS_PROTOCOL=http

# API behaviour
RESET_DB=0
USE_ALEMBIC=1
TZ=Asia/Jerusalem
```

Frontend build-time variables (baked into the Nginx image at build time):

```env
VITE_API_URL=http://192.168.1.30:8000
VITE_CMS_MODE=census         # mock | live | census
VITE_CENSUS_URL=http://192.168.1.30:8001
```

For production, copy `.env.prod.example` to `.env.prod` and fill in real values. The deploy workflow copies it to `.env` before running compose.

> **RESET_DB=1** drops all tables and deletes all data on the next startup. Always keep it at `0` in production.

> **USE_ALEMBIC=1** runs `alembic upgrade head` automatically before `uvicorn` starts. Set to `0` in the SSOT stack where schema is managed by Census.

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

The system has four roles with a strict hierarchy:

```
super_admin  >  admin  >  agent  >  viewer
```

### super_admin

- Full access to everything
- Can create users of all roles (admin, agent, viewer)
- Only role that can **create** new meetings
- Can update meeting passwords
- Sees all users including other super_admins
- Can delete any user (except themselves)

### admin

- Can create agent and viewer users
- Can manage groups: create, update, delete
- Can add/remove members to/from groups with an access level
- Can assign meetings to groups
- Can update and delete existing meetings
- Cannot create new meetings
- Cannot see or manage super_admin users

### agent

- Can see only the groups they belong to
- Can see only meetings whose type matches their access level in that group
- Can add `viewer` users to groups they belong to (viewers only)
- Cannot create users, meetings, or groups

### viewer

- Most restricted role
- Can see users only from within their own groups
- Can view meetings accessible to them by group membership rules
- Can see meeting passwords when available
- In blast dial meetings with no password, the UI shows "-"
- Cannot create or manage anything

---

## Access Level System

When an admin adds a user (agent or viewer) to a group, they must assign one of four access levels:

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

All endpoints require a `Bearer` JWT token in the `Authorization` header, unless stated otherwise.

### Auth

| Method | Endpoint        | Auth     | Description                             |
| ------ | --------------- | -------- | --------------------------------------- |
| POST   | `/auth/login`   | None     | Login with s_id + password, returns JWT |
| GET    | `/protected/me` | Any role | Returns current user details            |

**Login request body:**

```json
{
  "s_id": "superadmin",
  "password": "superadminpassword"
}
```

**Login response:**

```json
{
  "token": "eyJhbGciOiJIUzI1NiJ9...",
  "role": "super_admin"
}
```

---

### Users

| Method | Endpoint                       | Auth               | Description                                              |
| ------ | ------------------------------ | ------------------ | -------------------------------------------------------- |
| GET    | `/users/all`                   | All roles          | Get users list (viewer sees only users from same groups) |
| GET    | `/users/{s_id}`                | All roles          | Get a specific user                                      |
| POST   | `/users/create-agent`          | admin, super_admin | Create an agent user                                     |
| POST   | `/users/create-viewer`         | admin, super_admin | Create a viewer user                                     |
| POST   | `/users/create-admin`          | super_admin only   | Create an admin user                                     |
| DELETE | `/users/{user_id}`             | admin, super_admin | Delete a user                                            |
| GET    | `/users/group/{uuid}/meetings` | All roles          | Get meetings for a group by access level                 |

---

### Groups

| Method | Endpoint                                                         | Auth                                     | Description                                                             |
| ------ | ---------------------------------------------------------------- | ---------------------------------------- | ----------------------------------------------------------------------- |
| POST   | `/groups/create`                                                 | admin, super_admin                       | Create a new group                                                      |
| GET    | `/groups/all`                                                    | All roles                                | List all groups (agents see only their own)                             |
| GET    | `/groups/{group_uuid}/members`                                   | All roles                                | Get members of a group (agent/viewer only if they belong to that group) |
| GET    | `/groups/{group_uuid}`                                           | admin, super_admin                       | Get a single group                                                      |
| PUT    | `/groups/{group_uuid}`                                           | admin, super_admin                       | Update group name                                                       |
| DELETE | `/groups/{group_uuid}`                                           | admin, super_admin                       | Delete a group                                                          |
| POST   | `/groups/{group_uuid}/add-member/{user_uuid}?access_level=audio` | admin, super_admin, agent (viewers only) | Add user to group                                                       |
| POST   | `/groups/{group_uuid}/remove-member/{user_uuid}`                 | admin, super_admin                       | Remove user from group                                                  |
| POST   | `/groups/{group_uuid}/add-meeting/{meeting_uuid}`                | admin, super_admin                       | Link a meeting to a group                                               |
| POST   | `/groups/{group_uuid}/remove-meeting/{meeting_uuid}`             | admin, super_admin                       | Unlink a meeting from a group                                           |

---

### Meetings

| Method | Endpoint                            | Auth                                        | Description                                     |
| ------ | ----------------------------------- | ------------------------------------------- | ----------------------------------------------- |
| GET    | `/meetings/all_meetings`            | All roles (filtered by role + group access) | Get meetings (supports `?access_level=` filter) |
| GET    | `/meetings/{meeting_uuid}`          | All roles (access checks apply)             | Get a single meeting                            |
| POST   | `/meetings/create_meeting`          | admin, super_admin                          | Create a meeting (accessLevel in body)          |
| PUT    | `/meetings/{meeting_uuid}`          | admin, super_admin                          | Update a meeting (name / password)              |
| DELETE | `/meetings/{meeting_uuid}`          | admin, super_admin                          | Delete a meeting                                |
| GET    | `/meetings/number/{number}`         | admin, super_admin                          | Find meeting by number                          |
| PUT    | `/meetings/number/{meeting_number}` | admin, super_admin                          | Update meeting by number                        |
| GET    | `/meetings/group/{group_uuid}`      | admin, super_admin                          | Get meetings for a group                        |

**Create meeting request body:**

```json
{
  "m_number": "891234",
  "accessLevel": "audio",
  "password": "optional-password"
}
```

### Favorites

| Method | Endpoint                             | Auth      | Description                                                         |
| ------ | ------------------------------------ | --------- | ------------------------------------------------------------------- |
| GET    | `/favorites/meetings`                | All roles | List current user's favorite meetings (with password, participants) |
| POST   | `/favorites/meetings/{meeting_uuid}` | All roles | Add a visible meeting to favorites                                  |
| DELETE | `/favorites/meetings/{meeting_uuid}` | All roles | Remove a meeting from favorites                                     |

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
| role | Enum | super_admin / admin / agent / viewer |

**groups**
| Column | Type | Notes |
|---|---|---|
| UUID | UUID PK | Auto-generated |
| name | String UNIQUE | Group name |

**meetings**
| Column | Type | Notes |
|---|---|---|
| UUID | UUID PK | Auto-generated |
| m_number | String UNIQUE | Meeting room number |
| accessLevel | Enum | audio / video / blast_dial |
| password | String nullable | Conference password |

**member_group_access**  
Composite primary key `(member_uuid, group_uuid, access_level)` — controls what a user can see in a specific group.

**user_group_association**  
Many-to-many join table between users and groups.

**meeting_group_association**  
Many-to-many join table between meetings and groups.

**favorite_meetings**  
Join table between users and meetings for personal favorites (`member_uuid`, `meeting_uuid`, `created_at`, unique by user+meeting).

### Relationships

```
User ——< user_group_association >—— Group
User ——< member_group_access >————  Group (with access_level)
Group —< meeting_group_association >—— Meeting
```

---

## Frontend Pages

| Path                   | Page                | Who can access                | Features                                                                                            |
| ---------------------- | ------------------- | ----------------------------- | --------------------------------------------------------------------------------------------------- |
| `/login`               | Login               | Everyone (unauthenticated)    | Basic authentication                                                                                |
| `/dashboard`           | Dashboard           | All roles                     | KPI stats, group activity snapshot                                                                  |
| `/users`               | User management     | All roles                     | Create users, edit user details (admin/super_admin), delete users, search & filter                  |
| `/groups`              | Group management    | All roles                     | Create/edit groups, manage members, add meetings                                                    |
| `/audio-meetings`      | Audio meetings      | Users with audio access level | Browse audio meetings, search                                                                       |
| `/video-meetings`      | Video meetings      | Users with video access level | Browse video meetings, search                                                                       |
| `/favorite-meetings`   | Favorite meetings   | All roles                     | Quick list of personal favorite meetings with password + participants                               |
| `/blast-dial-meetings` | Blast dial meetings | Users with blast_dial access  | Browse blast dial meetings, search                                                                  |
| `/reports`             | Reports             | super_admin only              | Server settings: audio/video/launch sections with host, IP, username, password (localStorage based) |
| `/profile`             | Profile             | All roles                     | Current user info                                                                                   |
| `/settings`            | Settings            | All roles                     | User preferences                                                                                    |
| `/help`                | Help                | All roles                     | Guidance & documentation                                                                            |

Routes are guarded by `ProtectedRoute` — any unauthenticated access redirects to `/login`.

The sidebar dynamically shows/hides meeting type links based on the current user's access levels, fetched on login from their group memberships.

---

## Authentication Flow

```
1. User submits s_id + password on /login
2. Frontend calls POST /auth/login
3. Backend verifies password against Argon2 hash in DB
4. Backend signs a JWT with: UUID, role, s_id (expires in 24h)
5. Frontend stores token in localStorage
6. AuthContext calls GET /protected/me to fetch full user object
7. All subsequent API calls send: Authorization: Bearer <token>
8. TokenValidator (FastAPI dependency) decodes JWT + verifies user exists in DB
9. On logout: token removed from localStorage, AuthContext state cleared
10. On page reload: AuthContext re-checks token via /protected/me
```

If the token is invalid or expired, all protected endpoints return `401`.

---

## Logging System

All significant actions (create, delete, update, errors) are recorded by `LoggerManager` in `logger.py`.

- Logs are written to daily directories: `./logs/DD-MM-YYYY/log.txt`
- Each `log.txt` auto-rotates by size (default 10 MB, up to 30 files per day)
- Old log directories are auto-deleted after 30 days
- Log writes go through a dedicated queue + thread to avoid blocking HTTP requests
- Every mutating API call (POST/PUT/DELETE) also emits an AUDIT entry with user, endpoint, status, and duration
- Timestamps use `Asia/Jerusalem` timezone
- Initialized once in `main.py` via `LoggerManager.initialize()`

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

The frontend switches CMS source via `VITE_CMS_MODE` in `Frontend/src/services/api.js`:

| Mode | Behaviour |
|------|-----------|
| `mock` | Uses local `src/mocks/cmsMeetings.js` — pre-seeded meeting objects, 300 ms simulated delay |
| `live` | Calls an external CMS server directly (configured via `VITE_CMS_URL` + `VITE_CMS_API_KEY`) |
| `census` | Calls the internal Census API at `VITE_CENSUS_URL` |

Expected Census / CMS endpoints:

- `GET /meetings`
- `GET /meetings/{meetingId}`
- `POST /meetings`
- `PUT /meetings/{meetingId}/password`
- `DELETE /meetings/{meetingId}`

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
