# Ingestion Failures Runbook

## Symptom: Upload returns 400 "File too large"

**Cause:** ZIP exceeds 50 MB (`MAX_UPLOAD_BYTES`).

**Fix:** Trim repo (exclude `node_modules`, `.git`, build artifacts) before zipping.

---

## Symptom: Upload returns 400 "Repository exceeds max file limit"

**Cause:** More than `MAX_FILES_PER_REPO` supported files (default 5000).

**Fix:** Raise env `MAX_FILES_PER_REPO` or upload a filtered subset.

---

## Symptom: Async job status `failed`

**Steps:**

1. `GET /ingestion/status/{job_id}` — read `error` field.
2. Check backend logs for pipeline stack trace.
3. Common causes: corrupt ZIP, unsafe path entries, parse errors on binary files mis-detected as text.

**Fix:** Re-upload; ensure ZIP root contains source files (not a single nested folder without paths).

---

## Symptom: GitHub clone fails

**Cause:** Private repo without OAuth token, invalid URL, or network.

**Fix:**

1. User signs in via GitHub OAuth (stores encrypted token in `oauth_tokens`).
2. Use HTTPS URL: `https://github.com/org/repo`.
3. Verify `SECRET_KEY` is stable (token vault uses it for Fernet encryption).

---

## Symptom: Graph quality tier `low`

**Cause:** Unresolved imports (monorepo paths, dynamic imports).

**Fix:** Not a hard failure — review `graph_quality_json.warnings` on the version. Improve resolver coverage in Phase 1 services.

---

## Symptom: Health check missing `alembic_version`

**Cause:** Migrations not applied.

**Fix:**

```bash
cd backend && alembic upgrade head
```

---

## Recovery checklist

- [ ] `GET /health` returns `status: ok`
- [ ] `alembic upgrade head` succeeds
- [ ] Sample ZIP upload completes with `ingestion_status: completed`
- [ ] Dashboard returns `graph_quality` with a tier
