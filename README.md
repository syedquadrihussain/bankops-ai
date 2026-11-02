# BankOps AI

BankOps AI is a learning and portfolio MVP demonstrating an agent-first workflow for researching and verifying fictional banking policies, followed by a recorded human review decision.

**Scope:** Synthetic data only. This is not a production banking system and must not be used to make real banking or compliance decisions.

## Current capabilities

- FastAPI endpoints for health checks, policy listing, policy lookup, keyword search, and policy-version comparison.
- A LangGraph research workflow with supervisor, research, verification, and human-review stages.
- Verification gating so results that fail verification are not presented as verified.
- Basic validation of policy JSON records, required fields, and duplicate policy/version pairs.
- A human review workflow that records approval or rejection decisions.
- Review records and an append-only audit log stored in SQLite.
- An optional AI summary step that runs only after verification passes, with a fail-safe if the model is unavailable.
- Automated tests for the review workflow and other covered application behavior.

## Technology

- Python
- FastAPI and Pydantic
- LangGraph
- Ollama (local model, optional)
- SQLite
- PyJWT and scrypt password hashing
- pytest

## Run locally

From the project root, activate your virtual environment if needed, then run:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for interactive API documentation.

## Optional AI summaries

By default the project uses a fake model, so tests and demos need no model and no API key. To try a local model:

```powershell
ollama pull qwen2.5:3b
$env:LLM_PROVIDER = "ollama"
python -m uvicorn app.main:app --reload
```

Summaries are generated only for results that passed verification. They are labeled AI-generated and returned beside the original policy fields, never instead of them. If the model is unavailable, the verified results are still returned. Small local models can leave out or change details, so always compare a summary with the policy text.

## Login and roles

Most endpoints need a login token. Users are stored in SQLite with salted `scrypt` password hashes. There are two roles: `analyst` (can run research and read reviews) and `reviewer` (can also approve or reject). Tokens are JWTs signed with `HS256` and expire after 30 minutes.

```powershell
$env:JWT_SECRET = python -c "import secrets; print(secrets.token_urlsafe(48))"
python -m app.manage_users
python -m uvicorn app.main:app --reload
```

Log in with `POST /login`, then send the token as `Authorization: Bearer <token>`. In `/docs`, use the Authorize button and paste only the token. The app refuses to issue tokens if `JWT_SECRET` is missing or shorter than 32 characters. The secret must never be committed to Git.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/login` | Log in and receive an access token |
| GET | `/policies` | List synthetic policies |
| GET | `/policies/{policy_id}` | Retrieve the latest policy version |
| GET | `/policies/{policy_id}/compare` | Compare the two newest versions, when available |
| GET | `/search?q=identity` | Keyword search |
| POST | `/research` | Run research and verification; create a pending review when applicable |
| GET | `/reviews/{review_id}` | Retrieve a review record |
| POST | `/reviews/{review_id}/decision` | Record an approval or rejection |
| GET | `/reviews/{review_id}/audit` | List audit events for a review |

## Human review workflow

1. Log in with `POST /login`, then submit a research request to `POST /research` with your token.
2. When matching results pass verification, the response includes a `review_id` and `review_status: "pending_review"`.
3. A user with the `reviewer` role submits a decision to `POST /reviews/{review_id}/decision`.

Example decision request:

```json
{
  "decision": "approve"
}
```

Use `"reject"` instead of `"approve"` to record a rejection. The reviewer name is taken from your login token, not from the request body.

The application returns the recorded decision and status. A decision cannot be submitted again for a review that has already been decided.

**Important implementation limitations:**

- Review records and audit events are stored in a local SQLite file (`data/bankops.db`), so they survive restarts. SQLite suits a single machine, not a multi-server deployment.
- Tokens are checked by their signature only. A deleted user's token keeps working until it expires (30 minutes), and tokens cannot be revoked.
- The audit log is append-only at the application and database level (triggers block UPDATE and DELETE), but it is not tamper-proof: someone with direct access to the database file could change it.
- Recording approval does not execute a banking action.

## Tests and validation

Run these commands from the project root:

```powershell
python -m pytest -q
python -m pip check
```

The human-review implementation was manually exercised in Swagger, and the automated suite reported 88 passing tests at the time of the latest validation. Re-run the checks after any code or documentation changes.

## Known limitations and future work

- Search currently uses basic keyword matching; hybrid FAISS and BM25 retrieval has not been established as implemented.
- Policy comparison reports field-level differences; it is not legal or compliance interpretation.
- Production authentication (an identity provider, login lockout, rate limits) and document-level authorization are not implemented. The policy list, policy lookup, search and compare endpoints are public because the data is synthetic.
- Tamper-resistant audit storage, deployment hardening, and multi-server review storage are not implemented.
- Prompt-injection defenses, a dedicated security evaluation suite, and a formal evaluation runner require further verification before being claimed as implemented.
- A Streamlit interface and Docker packaging are not documented as completed features.
- AI summaries are not automatically checked against the policy text; a small model can omit a rule.

## Safety

All policy content is synthetic and intended for demonstration and learning only. Do not treat results as real regulatory guidance. No real banking or compliance decisions are made, and no banking action is executed.
