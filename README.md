\# BankOps AI — Agent-Based Banking Policy Research



BankOps AI is a portfolio proof of concept built with Python, FastAPI, and LangGraph. It demonstrates a structured workflow for researching synthetic banking policies and verifying retrieved results before returning them through an API.



\*\*Disclaimer:\*\* This project uses synthetic data for educational and demonstration purposes only. It is not intended for real banking, compliance, or financial decisions.



\## Project Overview



The application uses three workflow stages:



1\. \*\*Supervisor:\*\* Validates the incoming research question.

2\. \*\*Research:\*\* Searches synthetic banking policies using keyword matching.

3\. \*\*Verification:\*\* Checks whether each result contains the required policy fields.



If verification fails, the API does not return the results as verified.



\## Key Features



\- REST API built with FastAPI.

\- Workflow orchestration using LangGraph.

\- Synthetic banking policies stored in JSON.

\- Keyword-based policy search.

\- Input validation using Pydantic.

\- Required-field verification.

\- Error handling for missing policies and invalid requests.

\- Automated testing using Pytest.

\- Interactive API documentation through Swagger UI.



\## Technology Stack



\- Python

\- FastAPI

\- LangGraph

\- Pydantic

\- JSON

\- Pytest

\- Uvicorn



\## Architecture



```text

Client Request

&#x20;     |

&#x20;     v

&#x20;  FastAPI

&#x20;     |

&#x20;     v

&#x20; Supervisor

&#x20;     |

&#x20;     v

&#x20;   Research

&#x20;     |

&#x20;     v

&#x20; Verification

&#x20;     |

&#x20;     v

Verified Results

or Verification Failure

```



\## Project Structure



```text

BankOPSAI\_New/

├── app/

│   ├── \_\_init\_\_.py

│   ├── config.py

│   ├── main.py

│   ├── policy\_store.py

│   └── research\_graph.py

├── data/

│   └── policies.json

├── tests/

│   ├── test\_main.py

│   ├── test\_policy\_store.py

│   ├── test\_policy\_store\_errors.py

│   └── test\_research\_graph.py

├── .env.example

├── .gitignore

├── requirements.txt

└── README.md

```



\## Getting Started



\### Prerequisites



\- Python 3.13 or a compatible version

\- Git



\### 1. Clone the repository



```powershell

git clone https://github.com/syedquadrihussain/bankops-ai.git

cd bankops-ai

```



\### 2. Create a virtual environment



```powershell

python -m venv .venv

```



\### 3. Activate the environment



```powershell

.\\.venv\\Scripts\\Activate.ps1

```



\### 4. Install dependencies



```powershell

python -m pip install -r requirements.txt

```



\### 5. Run the application



```powershell

python -m uvicorn app.main:app --reload

```



The API is normally available at:



\- \*\*API:\*\* http://127.0.0.1:8000

\- \*\*Swagger UI:\*\* http://127.0.0.1:8000/docs



\## API Endpoints



| Method | Endpoint | Purpose |

|---|---|---|

| GET | `/health` | Check API health |

| GET | `/policies` | List synthetic policies |

| GET | `/policies/{policy\_id}` | Retrieve a policy by ID |

| GET | `/search?q=identity` | Search policies by keyword |

| POST | `/research` | Run the research workflow |



\## Example Research Request



Send a POST request to `/research` with this JSON body:



```json

{

&#x20; "question": "identity verification",

&#x20; "limit": 5

}

```



The workflow searches the policy dataset and verifies required fields before returning results as verified.



\## Running Tests



From the project root, run:



```powershell

python -m pytest -v

```



\*\*Development test result:\*\* 24 tests passed.



The tests cover API behavior, policy retrieval, keyword search, invalid inputs, file-loading errors, workflow execution, and verification failures.



\## Current Limitations



\- The application uses synthetic policy data only.

\- Search uses keyword matching rather than semantic search.

\- The current implementation does not use an LLM to generate research answers.

\- Verification checks required fields; it does not independently establish the factual correctness of policy content.

\- Production authentication, role-based access control, and deployment hardening are not implemented.

\- The application has not been validated for production banking or compliance use.



\## Potential Future Enhancements



\- Retrieval-augmented generation (RAG).

\- Policy version comparison and conflict detection.

\- Citation and evidence verification.

\- Human approval workflows.

\- Access controls and audit logging.

\- Expanded security and evaluation tests.



These are potential enhancements, not features claimed as implemented.



\## Author



\*\*Syed Quadri\*\*



\- GitHub Profile: https://github.com/syedquadrihussain

\- BankOps AI Repository: https://github.com/syedquadrihussain/bankops-ai

\- RecruitOS AI Repository: https://github.com/syedquadrihussain/recruitos-ai

