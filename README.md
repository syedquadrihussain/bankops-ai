# BankOps AI

BankOps AI is a learning and portfolio MVP for an agent-first banking operations and compliance workflow. It uses **fictional synthetic policy data only**.

## Current capabilities

- FastAPI endpoints for health, policy listing, policy lookup, and keyword search.
- A LangGraph research workflow with supervisor/research/verification steps.
- A verification gate that suppresses results when verification fails.
- Basic validation of policy JSON records, required fields, and duplicate policy/version pairs.
- A demonstration comparison of the two newest versions of a policy.

## Run locally

Activate the project's virtual environment, then run:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for interactive API documentation.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/policies` | List all synthetic policies |
| GET | `/policies/{policy_id}` | Return the latest version of a policy |
| GET | `/policies/{policy_id}/compare` | Compare the two newest versions, when available |
| GET | `/search?q=identity` | Keyword search |
| POST | `/research` | Run the research and verification workflow |

## Test

```powershell
python -m pytest -v
python -m pip check
```

## Safety and limitations

- This project is a demonstration and learning artifact, not a production banking system.
- All policy content is synthetic and must not be treated as real compliance guidance.
- Search is basic keyword matching, not semantic retrieval.
- Policy comparison reports field-level differences for the two newest versions; it is not a legal or compliance interpretation.
- Authentication, role-based access control, production-grade audit storage, and deployment hardening are not implemented.
- Human authorization and review remain necessary before any real-world action. No real banking action is performed by this MVP.

## Human Review Gate

The `/research` workflow performs field verification on matching synthetic
banking policies. When verification passes, the response includes
`review_status: "pending_review"` to indicate that human review is still
required.

- `pending_review`: matching results passed field verification and await review.
- `not_required`: no matching results were found, or review was not applicable.
- Verification failures do not return results as verified.

This is a portfolio demonstration status marker. It does not implement
authenticated reviewer approval, persistent approval records, or real banking
actions. All data is synthetic; human review is required before any real-world
use.
