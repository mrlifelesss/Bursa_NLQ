# Bursa NLQ

Full-stack project for the TASE natural-language query experience. The repo bundles a Vite/React frontend and the FastAPI service that powers NLQ parsing, company/report suggestions, and DynamoDB lookups.

## Structure
- `nlq-for-tase-announcements/` – customer-facing React app built with Vite.
- `server.py` – FastAPI entry point that exposes `/announcements`, `/company-suggestions`, and related endpoints.
- `nlq_parser_v5/` – reusable NLQ parsing engine and data files (aliases, prompts, etc.) shared by the backend.
- `requirements.txt` – Python dependencies for the server plus parser package.
- `amplify.yml` – default build specification for AWS Amplify static hosting.

## Prerequisites
- Node.js 20.x (or 18.x LTS) and npm.
- Python 3.11+ (tested) with the ability to create virtual environments.
- Access to the target DynamoDB tables and, optionally, a Google Gemini API key if you plan to enable LLM-based parsing.

## Frontend (Vite)
```bash
cd scripts/Bursa_NLQ/nlq-for-tase-announcements
cp .env.example .env.local   # edit values as needed
npm install
npm run dev    # http://localhost:5173
# npm run build  # production bundle in dist/
```
Key env vars:
- `VITE_BACKEND_BASE` – base URL of the FastAPI service (e.g. `https://api.example.com`).
- `VITE_BACKEND_PROXY_TARGET` – used by `vite.config.ts` during local dev to proxy API calls (default `http://localhost:8000`).
- `GEMINI_API_KEY` – optional; only required if you enable Gemini-powered parsing paths.

## Backend (FastAPI + NLQ parser)
```bash
cd scripts/Bursa_NLQ
python -m venv .venv
. .venv/Scripts/activate   # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn server:app --reload --port 8000
```
The server expects AWS credentials (via environment variables or profiles) with access to DynamoDB tables referenced in `DEFAULT_QUERY_CONFIG`. Configure alternate table names or endpoints via the request payloads (`/announcements`, `/parse-build-run`).

## Deploying with AWS Amplify
- Connect the repository in Amplify Hosting.
- Set the App root to the repo root, keep the default build spec (`amplify.yml`).
- Define environment variables for the frontend (`VITE_BACKEND_BASE`, `GEMINI_API_KEY`, etc.).
- Amplify will run `npm ci` and `npm run build` inside `nlq-for-tase-announcements/` and publish the `dist/` directory.
- If you expose the FastAPI service separately (e.g. Amplify backend, ECS, Lambda), update `VITE_BACKEND_BASE` accordingly.

## LLM Parsing
The parser integrates with Google Gemini when `google-genai` is installed and `GEMINI_API_KEY` is set. Without it, heuristics-only parsing remains active.

## Tips
- `npm run lint` / `npm run build` before pushing to catch type or syntax issues.
- Keep `node_modules/`, `dist/`, `__pycache__/`, and secrets out of git (handled by `.gitignore`).
- Large alias datasets are already tracked in `nlq_parser_v5/`; prune or swap them for lighter subsets if needed for public repos.
