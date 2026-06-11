# GitHub PR Review Assistant

An AI-powered pull request review tool that integrates with the GitHub API and an LLM (Anthropic Claude / OpenAI) to automatically analyze diffs, surface issues, and post inline review comments — triggered manually via CLI or automatically via GitHub Webhooks.

---

## ✨ Features

- 🔍 **Automated PR analysis** — fetches diffs and metadata directly from the GitHub API
- 🧠 **LLM-powered review** — sends code changes to Claude or GPT for intelligent feedback
- 💬 **Inline GitHub comments** — posts review suggestions directly on specific lines
- 🪝 **Webhook support** — auto-triggers on `pull_request` events (opened, synchronize)
- 🖥️ **CLI mode** — manually review any PR by URL without running a server
- 🔒 **Secure** — validates GitHub webhook signatures (`X-Hub-Signature-256`)
- 🧩 **Modular architecture** — swap LLM providers or extend GitHub logic independently

---

## 📁 Project Structure

```
github-pr-review-assistant/
│
├── app/
│   ├── __init__.py                  # App factory
│   ├── config.py                    # Env vars, tokens, settings
│   │
│   ├── api/
│   │   ├── routes.py                # REST endpoints: /review, /webhook, /health
│   │   └── schemas.py               # Request/response models (Pydantic)
│   │
│   ├── github/
│   │   ├── client.py                # GitHub API wrapper
│   │   ├── parser.py                # PR diff + metadata parser
│   │   └── webhook.py               # Webhook signature validation & event handling
│   │
│   ├── llm/
│   │   ├── client.py                # LLM API wrapper (Anthropic / OpenAI)
│   │   ├── prompts.py               # Prompt templates for PR review
│   │   └── reviewer.py              # Diff → prompt → LLM → structured review
│   │
│   └── services/
│       ├── review_service.py        # End-to-end: fetch → review → comment
│       └── comment_service.py       # Format & post GitHub review comments
│
├── tests/
│   ├── test_github/
│   ├── test_llm/
│   └── test_api/
│
├── scripts/
│   └── review_pr.py                 # CLI: python scripts/review_pr.py <PR_URL>
│
├── .env.example
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- A GitHub account with a [Personal Access Token](https://github.com/settings/tokens) (scopes: `repo`, `pull_requests`)
- An API key for your LLM provider (Anthropic or OpenAI)
- (Optional) A public URL for webhook support — use [ngrok](https://ngrok.com/) for local dev

### 1. Clone the repository

```bash
git clone https://github.com/saket-pathak/github-pr-review-assistant.git
cd github-pr-review-assistant
```

### 2. Set up environment

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
# GitHub
GITHUB_TOKEN=ghp_your_token_here

# LLM Provider — choose one
ANTHROPIC_API_KEY=sk-ant-your_key_here
OPENAI_API_KEY=sk-your_key_here          # if using OpenAI
LLM_PROVIDER=anthropic                   # "anthropic" or "openai."

# Webhook (optional)
GITHUB_WEBHOOK_SECRET=your_webhook_secret

# Server
PORT=8000
DEBUG=false
```

### 4. Run the server

```bash
# FastAPI
uvicorn app:create_app --reload --port 8000

# or Flask
flask run --port 8000
```

---

## 🖥️ CLI Usage

Review any pull request directly from your terminal — no server needed:

```bash
python scripts/review_pr.py https://github.com/owner/repo/pull/42
```

The script will:
1. Fetch the PR diff from GitHub
2. Send it to the configured LLM
3. Print a structured review to stdout
4. (Optional) Post comments back to GitHub if `--post` is passed

```bash
python scripts/review_pr.py https://github.com/owner/repo/pull/42 --post
```

---

## 🪝 Webhook Setup

To trigger automatic reviews when a PR is opened or updated:

1. In your GitHub repo, go to **Settings → Webhooks → Add webhook**
2. Set **Payload URL** to `https://your-domain.com/webhook`
3. Set **Content type** to `application/json`
4. Add a **Secret** (must match `GITHUB_WEBHOOK_SECRET` in `.env`)
5. Select event: **Pull requests**

For local development with ngrok:

```bash
ngrok http 8000
# Use the generated https URL as your webhook payload URL
```

---

## 🌐 API Endpoints

| Method | Endpoint   | Description                          |
|--------|------------|--------------------------------------|
| `POST` | `/review`  | Manually trigger a review for a PR   |
| `POST` | `/webhook` | GitHub webhook receiver              |
| `GET`  | `/health`  | Health check                         |

### `POST /review` — Request body

```json
{
  "repo": "owner/repo-name",
  "pr_number": 42
}
```

### `POST /review` — Response

```json
{
  "status": "success",
  "pr": 42,
  "comments_posted": 5,
  "summary": "The PR introduces X. Key concerns: ..."
}
```

---

## 🧠 How It Works

```
GitHub Webhook / CLI
        │
        ▼
  api/routes.py              ← HTTP entry point
        │
        ▼
  services/review_service.py ← Orchestrates the full flow
       ┌─────────────────────┐
       │                     │
       ▼                     ▼
github/client.py       llm/reviewer.py
github/parser.py       llm/prompts.py
       │                     │
       └──────────┬──────────┘
                  ▼
     services/comment_service.py  ← Posts inline review comments to GitHub
```

1. **Fetch** — `github/client.py` pulls PR metadata and raw diff via the GitHub REST API
2. **Parse** — `github/parser.py` extracts file-level hunks, added/removed lines, and language hints
3. **Review** — `llm/reviewer.py` chunks large diffs and sends each to the LLM with a structured prompt
4. **Comment** — `services/comment_service.py` maps LLM feedback back to line numbers and posts inline GitHub review comments

---

## 🐳 Docker

```bash
# Build and start
docker-compose up --build

# Run in background
docker-compose up -d
```

The app will be available at `http://localhost:8000`.

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

Run a specific module:

```bash
pytest tests/test_llm/ -v
pytest tests/test_github/ -v
```

---

## ⚙️ Configuration Reference

| Variable               | Required | Default      | Description                                  |
|------------------------|----------|--------------|----------------------------------------------|
| `GITHUB_TOKEN`         | ✅ Yes   | —            | GitHub Personal Access Token                 |
| `ANTHROPIC_API_KEY`    | ✅*      | —            | Anthropic API key (`*` if using Anthropic)   |
| `OPENAI_API_KEY`       | ✅*      | —            | OpenAI API key (`*` if using OpenAI)         |
| `LLM_PROVIDER`         | No       | `anthropic`  | LLM backend: `anthropic` or `openai`         |
| `GITHUB_WEBHOOK_SECRET`| No       | —            | For validating webhook signatures            |
| `PORT`                 | No       | `8000`       | Server port                                  |
| `DEBUG`                | No       | `false`      | Enable debug logging                         |

---

## 🛣️ Roadmap

- [ ] Support for GitLab and Bitbucket
- [ ] Per-language review rules (stricter for Python, lenient for config files)
- [ ] Review history dashboard (React frontend)
- [ ] GitHub App distribution (no PAT required)
- [ ] Caching layer to avoid re-reviewing unchanged files

---

## 🤝 Contributing

Contributions are welcome! Please open an issue first to discuss what you'd like to change.

```bash
git checkout -b feature/your-feature-name
# make your changes
git commit -m "feat: describe your change."
git push origin feature/your-feature-name
# open a Pull Request
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 👤 Author

**Saket Pathak**
- GitHub: [@saket-pathak](https://github.com/saket-pathak)
- LinkedIn: [linkedin.com/in/saket-pathak-34875128b](https://linkedin.com/in/saket-pathak-34875128b)
