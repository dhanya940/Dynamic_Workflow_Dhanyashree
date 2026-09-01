# Dynamic Workflow Automation System — Complete Tasks 1–6

This package follows the supplied project specification and includes the backend **and** the frontend flow.

## Task coverage

### Task 1 — Project Setup
- FastAPI application
- PostgreSQL + SQLAlchemy
- Alembic migrations
- `.env` configuration
- Organized `models`, `schemas`, `services`, `routers`, `database`, `core`
- Startup database connection verification

### Task 2 — Database Schema
Implemented:
- `forms`
- `form_versions`
- `fields`
- `field_options`
- `conditional_rules`
- `submissions`
- `response_values`
- `users`
- `form_share_links` (supporting table required to store the Task 6 slug)

An initial Alembic migration is included, so you do not need to generate the first migration yourself.

### Task 3 — Authentication
Frontend pages:
- Signup
- Signin
- Home

Backend:
- `POST /auth/signup`
- `POST /auth/signin`
- `GET /auth/home`

Passwords are hashed and signin returns a JWT bearer token.

### Task 4 — Form Management
Backend:
- `POST /forms`
- `GET /forms`
- `GET /forms/{id}`
- `PUT /forms/{id}`
- `PATCH /forms/{id}/archive`
- `POST /forms/{id}/fields`
- `PUT /fields/{id}`
- `DELETE /fields/{id}`
- `PATCH /forms/{id}/reorder-fields`

Frontend:
- Form list
- Search
- Create form
- Form builder
- Add/delete/edit fields
- Required-field configuration
- Field types
- Dropdown/checkbox options
- Field ordering with Up/Down controls
- Edit form
- Archive confirmation

### Task 5 — Versioning & Publishing
Backend:
- `POST /forms/{id}/publish`
- `GET /forms/{id}/versions`
- `GET /forms/{id}/versions/{version_number}`

Frontend:
- Publish button
- Version history
- Version details
- Read-only historical versions

Published versions are immutable. Editing a published form branches a new draft version. Old versions remain available for old responses.

### Task 6 — Shareable Form Access
Backend:
- `POST /forms/{id}/generate-link`
- `GET /public/forms/{slug}`
- `POST /public/forms/{slug}/submit`

Frontend:
- Share action
- Copyable public URL
- Public dynamic form
- Responsive fields
- Form status/error handling
- Dynamic conditional show/hide rules
- Submission confirmation

The API path required by the specification remains `/public/forms/{slug}`. The browser-friendly share page is `/form/{slug}` and calls that API.

## Exact high-level flow

1. User opens the application.
2. User signs up.
3. User signs in.
4. Home page opens.
5. User opens **Forms**.
6. User clicks **Create Form**.
7. User enters title + description.
8. `POST /forms` creates the form.
9. User is taken to the **Form Builder**.
10. User adds fields.
11. User edits field labels/types/required status/options/validation.
12. User reorders fields.
13. User can create conditional rules such as `Experience = Yes -> show Years of Experience`.
14. User clicks **Publish**.
15. A published snapshot (v1, v2, ...) is created/activated.
16. User can open **Version History** and inspect read-only versions.
17. User clicks **Share**.
18. A unique public link is generated for the active published version.
19. A public user opens the link.
20. The public page retrieves the published schema and renders fields dynamically.
21. Conditional rules show/hide fields.
22. Public user clicks **Submit**.
23. A submission parent is stored in `submissions`.
24. Individual answers are stored in `response_values`.
25. When the owner edits a published form, a new draft is branched; the old published version remains unchanged.
26. Publishing the new draft creates the next active version.
27. Previous public links point to their old versions and become unavailable when those versions are no longer active, preserving the versioning rule.

## Run on Windows

### 1. PostgreSQL
Create a PostgreSQL database and user matching your `.env`.

Example values:
- database: `workflow_db`
- user: `workflow_user`
- host: `localhost`
- port: `5432`

### 2. Configure environment

Copy:

```text
.env.example
```

to:

```text
.env
```

Then put your real PostgreSQL password in `DATABASE_URL`.

Example:

```text
DATABASE_URL=postgresql://workflow_user:YOUR_PASSWORD@localhost:5432/workflow_db
SECRET_KEY=replace-with-a-long-random-secret
```

Do not commit `.env`.

### 3. Create virtual environment

From this folder:

```powershell
python -m venv venv
venv\Scripts\activate
```

### 4. Install packages

```powershell
pip install -r requirements.txt
```

### 5. Create database tables

```powershell
alembic upgrade head
```

### 6. Start the application

```powershell
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

## Important

If PostgreSQL gives:

`password authentication failed for user "workflow_user"`

then the application code is not the cause. Check that the username/password/database in `.env` exactly match the PostgreSQL account, and restart the backend after changing `.env`.

## Project structure

```text
Dynamic-Workflow-Automation-System/
├── app/
│   ├── core/
│   ├── database/
│   ├── models/
│   ├── routers/
│   ├── schemas/
│   ├── services/
│   └── main.py
├── alembic/
│   └── versions/
│       └── 0001_initial.py
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── .env.example
├── alembic.ini
├── requirements.txt
└── README.md
```

## Note about additions

The supplied PDF names the database structures and the frontend/public Submit experience, but does not explicitly name a submission API endpoint, field-update endpoint, or conditional-rule CRUD endpoint. Those small supporting endpoints are included so the documented end-to-end flow is actually usable rather than stopping at a mock UI.
