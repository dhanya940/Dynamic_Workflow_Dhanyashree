# Endpoint checklist

## Task 3
POST /auth/signup
POST /auth/signin
GET  /auth/home

## Task 4
POST   /forms
GET    /forms
GET    /forms/{id}
PUT    /forms/{id}
PATCH  /forms/{id}/archive
POST   /forms/{id}/fields
PUT    /fields/{id}
DELETE /fields/{id}
PATCH  /forms/{id}/reorder-fields

## Supporting dynamic rules
POST   /forms/{id}/rules
GET    /forms/{id}/rules
DELETE /forms/rules/{rule_id}

## Task 5
POST /forms/{id}/publish
GET  /forms/{id}/versions
GET  /forms/{id}/versions/{version_number}

## Task 6
POST /forms/{id}/generate-link
GET  /public/forms/{slug}
POST /public/forms/{slug}/submit
