# Ubuntu Standalone + CMS Lab - Deployment Skeleton

This repository now includes a CI/CD and deployment skeleton for Ubuntu.

## 1. What was added

- CI workflow: .github/workflows/ci.yml
- Deploy workflow (SSH): .github/workflows/deploy-ubuntu.yml
- Production compose: docker-compose.prod.yml
- Production Dockerfiles:
  - Backend/Dockerfile.prod
  - Frontend/Dockerfile.prod
- Frontend nginx config: Frontend/nginx.conf
- Backend test skeleton:
  - Backend/tests/test_hash_helper.py
  - Backend/requirements-dev.txt
- Production env template: .env.prod.example
- CMS switching support in frontend API service:
  - Frontend/src/services/api.js

## 2. Ubuntu server prerequisites

Install Docker and Compose plugin:

sudo apt update
sudo apt install -y docker.io docker-compose-plugin git
sudo systemctl enable --now docker

## 3. Server setup

1. Choose a deploy path (default used in workflow): /opt/meet-control
2. Create .env.prod in the deploy path based on .env.prod.example
3. Set values for:
   - DB creds
   - JWT secret
   - super admin credentials
   - VITE_CMS_MODE=remote
   - VITE_CMS_URL=<your lab CMS URL>
   - VITE_CMS_API_KEY (if required)

## 4. GitHub secrets required

- DEPLOY_HOST
- DEPLOY_USER
- DEPLOY_SSH_KEY
- DEPLOY_PORT (optional, defaults to 22)
- DEPLOY_PATH (optional, defaults to /opt/meet-control)

## 5. How deploy works

On push to main (or manual workflow_dispatch):

1. SSH to Ubuntu server
2. Pull latest main
3. Copy .env.prod to .env
4. Run docker compose -f docker-compose.prod.yml up -d --build

## 6. CMS integration mode

In Frontend environment:

- VITE_CMS_MODE=mock -> use local mock data
- VITE_CMS_MODE=remote -> call real CMS API (VITE_CMS_URL)

Expected CMS endpoints in remote mode:

- GET /meetings
- GET /meetings/{meetingId}
- POST /meetings
- PUT /meetings/{meetingId}/password
- DELETE /meetings/{meetingId}

## 7. Notes

- Frontend env values are build-time variables in Dockerfile.prod.
- If CMS URL changes, redeploy frontend image.
- Current backend tests are a skeleton; extend with API and role-permission tests.
