# Project Avnet

Project Avnet is a meetings management platform with:

1. React + Vite frontend (`Meetings-App`)
2. FastAPI + SQLAlchemy backend (`project-avnet-main`)
3. PostgreSQL database (Docker)

The app supports role-based access (`super_admin`, `admin`, `agent`), mador-based ownership, meeting linking in SQL, and CMS detail retrieval on demand.

## Overview

### Frontend

1. Authentication with token + `/protected/me` role verification
2. Meetings pages: Audio, Video, Blastdial
3. Users page with role-aware creation and filtering
4. Mador management and member assignment
5. Meeting actions:
   - Add meeting (persists to DB)
   - Open meeting (fetches details from CMS mock)
   - Delete meeting (role-based)
   - Update password in CMS mock (role-based)

### Backend

1. JWT auth and role validation middleware
2. User CRUD endpoints (with role guards)
3. Mador endpoints and membership management
4. Meeting endpoints under mador routes
5. Startup initialization:
   - Create tables
   - Ensure super admin exists

## Current Meeting Data Flow

1. Meetings list pages load meeting links from database (`madors -> meetings`)
2. Add meeting writes to database first (`meeting_id`, `mador_id`, `mador_owner_id`)
3. After add, frontend fetches CMS data by `meeting_id` to enrich display
4. Open button fetches latest CMS details on demand
5. CMS includes metadata like `name`, `status`, `password`, participants, node

Note: SQL stores minimal link data, while detailed meeting metadata comes from CMS mock.

## Role Permissions

### super_admin

1. Can create admins and agents
2. Can delete any meeting
3. Can view and update any meeting password
4. Full access across madors

### admin

1. Can create agents
2. Can delete only meetings they own (mador ownership)
3. Can update password for owned/mapped meetings
4. Access limited by mador ownership/membership logic

### agent

1. Cannot create users
2. Cannot delete meetings
3. Cannot update meeting passwords
4. Can access permitted views based on assigned madors

## Tech Stack

### Backend

1. Python 3.11
2. FastAPI
3. SQLAlchemy
4. PostgreSQL
5. Passlib/JWT auth helpers

### Frontend

1. React
2. Vite
3. React Router
4. Axios

### Infrastructure

1. Docker Compose
2. PostgreSQL service (`db`)
3. API service (`api`)
4. Frontend service (`frontend`)

## Project Structure

```
project-avnet-main/
├── docker-compose.yml
├── README.md
├── Meetings-App/
│   ├── src/
│   │   ├── components/
│   │   │   ├── MeetingsPage.jsx
│   │   │   └── ProtectedRoute.jsx
│   │   ├── context/
│   │   │   └── AuthContext.jsx
│   │   ├── mocks/
│   │   │   └── cmsMeetings.js
│   │   ├── pages/
│   │   │   ├── AudioMeetings.jsx
│   │   │   ├── VideoMeetings.jsx
│   │   │   ├── BlastdialMeetings.jsx
│   │   │   ├── Users.jsx
│   │   │   └── ...
│   │   └── services/
│   │       └── api.js
│   └── ...
└── project-avnet-main/
    ├── main.py
    ├── requirements.txt
    └── app/
        ├── core/
        ├── models/
        ├── repository/
        ├── routers/
        ├── schema/
        ├── security/
        ├── service/
        └── util/
```

## Environment Variables

Create `.env` at the repository root:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=fastapi_demo
POSTGRES_HOST=db

JWT_SECRET=your_jwt_secret
JWT_ALGORITHM=HS256

SUPER_ADMIN_USERNAME=superadmin
SUPER_ADMIN_PASSWORD=superadminpassword

RESET_DB=
```

Optional:

1. Set `RESET_DB=1` to force full schema reset on startup
2. Keep empty for normal startup

## Run With Docker

```bash
docker-compose down -v
docker-compose up --build
```

Services:

1. Frontend: http://localhost:5173
2. API: http://localhost:8000
3. API docs: http://localhost:8000/docs

## API Reference (Current)

### Auth

1. `POST /auth/login`
2. `POST /auth/signup` (if enabled by current role flow)

### Protected

1. `GET /protected/me`

### Users

1. `GET /users/all`
2. `GET /users/{s_id}`
3. `POST /users/create-agent`
4. `POST /users/create-admin`
5. `DELETE /users/{user_id}`

### Madors

1. `POST /madors/`
2. `GET /madors/`
3. `POST /madors/{mador_id}/members/{user_id}`
4. `DELETE /madors/{mador_id}/members/{user_id}`
5. `POST /madors/{mador_id}/meetings`
6. `GET /madors/{mador_id}/meetings`

## Frontend Routes

1. `/` Login
2. `/dashboard`
3. `/audio-meetings`
4. `/video-meetings`
5. `/blastdial-meetings`
6. `/groups`
7. `/users`
8. `/profile`
9. `/reports`
10. `/help`
11. `/settings`

## Notes

1. The CMS layer is currently mocked in `Meetings-App/src/mocks/cmsMeetings.js`
2. Frontend verifies role from backend response, not only token storage
3. Meeting details are intentionally split:
   - SQL for linkage and ownership
   - CMS for dynamic meeting metadata

## 🐛 Troubleshooting

### Database Issues
- If tables don't exist, restart the API service to trigger auto-creation
- Check PostgreSQL logs for connection issues

### Frontend Issues
- Ensure backend is running on port 8000
- Check browser console for CORS errors
- Verify `VITE_API_URL` environment variable

### Docker Issues
- Use `docker compose down` to stop services
- Use `docker compose up --build` to rebuild images
- Check container logs with `docker compose logs`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and commit: `git commit -am 'Add feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For questions or support, please contact the development team or create an issue in the GitHub repository.

---

**Note**: This project automatically creates database tables on startup and initializes a super admin user for testing purposes.
