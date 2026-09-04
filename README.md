<div align="center">
  <h1>📈 App Review & Analytics</h1>
  <p>
    <strong>Fetch, analyze, and export user reviews and ratings from the Google Play Store and Apple App Store.</strong>
  </p>

  <p>
    <a href="#features">Features</a> •
    <a href="#tech-stack">Tech Stack</a> •
    <a href="#getting-started">Getting Started</a> •
    <a href="#deployment">Deployment</a> •
    <a href="#project-structure">Project Structure</a>
  </p>
</div>

---

## ✨ Features

- 🔍 **Search & Fetch**: Search for any app on either Google Play Store, Apple App Store, or both simultaneously. Select the target app to import its review data.
- ⏳ **Background Fetch Jobs**: Polling-based progress bar prevents long-running scraping tasks from blocking the UI, giving you real-time feedback on the fetch status.
- 📊 **Analytics Dashboard**: Beautiful charts visualizing **Rating Distribution**, **Sentiment Split**, and **Monthly Review Volume Trends**.
- 🎛️ **Interactive Filtering**: Search review contents via keywords, filter by exact rating and sentiment, or restrict data to specific date ranges.
- 🧠 **Sentiment Analysis**: Automatic sentiment scoring (Positive, Neutral, Negative) computed on the fly using Python's `TextBlob` library.
- 💾 **Export Capabilities**: Instantly download filtered reviews in structured **CSV** or **JSON** formats.

---

## 🛠 Tech Stack

- **Frontend:** React (Vite), TailwindCSS, Recharts
- **Backend:** Python, FastAPI, Uvicorn
- **Database:** SQLite
- **Scraping:** `google-play-scraper`, `app_store_scraper`
- **Deployment:** Docker, Fly.io

---

## 🚀 Getting Started

### Prerequisites

- Python 3.13+
- Node.js 18+ (with npm)
- Docker (optional, for deployment testing)

### Running in Development Mode

Run the backend and frontend separately for hot-reloading during development.

#### 1. Start the FastAPI Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000
```

#### 2. Start the React Frontend
```bash
cd frontend
npm install
npm run dev
```
Open your browser to [http://localhost:5173](http://localhost:5173).

---

### Running in Production Mode (Local)

FastAPI can serve the compiled React assets statically, running the entire application on a **single port (8000)**. This mirrors the production setup.

#### 1. Build the Frontend
```bash
cd frontend
npm run build
```

#### 2. Run the FastAPI Server
```bash
cd backend
DB_PATH=./review_data.db .venv/bin/uvicorn app.main:app --port 8000
```
Open your browser to [http://localhost:8000](http://localhost:8000).

---

## ☁️ Deployment (Fly.io)

This project is configured to deploy seamlessly to [Fly.io](https://fly.io) using a **Multi-Stage Dockerfile** and a **Persistent Volume** for SQLite.

1. **Install Fly CLI**
   Follow the [Fly.io installation guide](https://fly.io/docs/hands-on/install-flyctl/).

2. **Login to Fly.io**
   ```bash
   fly auth login
   ```

3. **Provision a Persistent Volume**
   Because cloud servers are ephemeral, we use a volume to ensure the SQLite database (`review_data.db`) persists across deployments.
   ```bash
   fly volumes create review_data_vol --region ewr --size 1
   ```

4. **Deploy the App**
   The deployment uses the configurations found in `Dockerfile` and `fly.toml`.
   ```bash
   fly deploy
   ```

5. **Open the App**
   ```bash
   fly open
   ```

---

## 🏗 Project Structure

```text
.
├── backend/               # FastAPI + Scrapers + Python Tests
│   ├── app/
│   │   ├── scrapers/      # Play Store and App Store scraping logic
│   │   ├── routers/       # API endpoints (apps, reviews, jobs)
│   │   ├── db.py          # SQLite database connection & queries
│   │   ├── main.py        # Application entrypoint & static serving
│   │   └── jobs.py        # Background workers for fetching reviews
│   └── tests/             # Pytest unit tests (37 tests)
│
├── frontend/              # Vite + React (SPA) + Vitest
│   ├── src/
│   │   ├── pages/         # SearchPage and DashboardPage views
│   │   ├── components/    # Reusable UI components and charts
│   │   └── __tests__/     # Frontend component & logic tests
│   └── dist/              # Built production static assets (created via npm run build)
│
├── Dockerfile             # Multi-stage Docker build config
├── fly.toml               # Fly.io deployment and volume configuration
└── README.md              # You are here!
```

---

## 🧪 Running Tests

### Backend Unit Tests (37 Tests)
```bash
cd backend
.venv/bin/pytest -v
```

### Frontend Unit Tests
```bash
cd frontend
npm run test
```
