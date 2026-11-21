# Verification Plan · SAT-0

**Story:** Client submits a project intake

**Gate 1 (clarifications):** all questions answered

**Tagging rule:** Every test that verifies a criterion names it in its title, e.g. 'SAT-0 AC-1 ...'

| AC | Criterion (as written) | Clarified as | Disposition | Checks |
|---|---|---|---|---|
| AC-1 | POST /api/intakes with a client name, a project type (ECOMMERCE, WEBSITE or API) and a description of at least 20 characters returns 201 with a reference like INT-1001 and status RECEIVED | Reference format: 'INT-' then digits (INT-1001 is the first). All three project types accepted. | verify | `AC-1.a` [maven-surefire:backend] API: POST with each project type and a 46-character description returns 201, reference INT-<digits>, status RECEIVED |
| AC-2 | A description shorter than 20 characters returns 400 with the error "Describe what you want in at least 20 characters" | Under 20 = 19 or fewer characters after trimming; exactly 20 is accepted. | verify | `AC-2.a` [maven-surefire:backend] API: a 19-character description returns 400 with the exact message; a 20-character one returns 201 |
| AC-3 | GET /api/intakes/{reference} returns the submitted intake, and an unknown reference returns 404 | — | verify | `AC-3.a` [maven-surefire:backend] API: GET by the reference just created returns the same name and type; GET INT-999999 returns 404 |
| AC-4 | On the intake page, submitting a valid form shows "Your reference is INT-" followed by the number | — | verify | `AC-4.a` [playwright:frontend] UI: fill name, type and a valid description, submit, see 'Your reference is INT-<digits>' (API and UI started by Playwright) |
| AC-5 | On the intake page, a description shorter than 20 characters shows the error message and keeps what the client typed | 'Keeps what the client typed' = name, type and description fields still hold the entered values after the error. | verify | `AC-5.a` [playwright:frontend] UI: a short description shows the exact error and the three fields keep their values |

## Expected evidence

- `AC-1.a`: junit: maven-surefire:backend
- `AC-2.a`: junit: maven-surefire:backend, response values
- `AC-3.a`: junit: maven-surefire:backend
- `AC-4.a`: junit: playwright:frontend (desktop), screenshot
- `AC-5.a`: junit: playwright:frontend (desktop), screenshot
