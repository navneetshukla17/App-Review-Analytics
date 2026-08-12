# 📈 Store Reviews Insights

Fetch, analyze, and export user reviews and ratings from the Google Play Store and Apple App Store (India locale).

## Features

- **Search & Fetch**: Search for any app on either Google Play Store, Apple App Store, or both simultaneously, and dynamically select which app you want to import.
- **Background Fetch Jobs**: Polling-based progress bar prevents long-running scraping tasks from blocking the UI.
- **Analytics Dashboard**: Beautiful charts visualizing Rating Distribution, Sentiment Split, and Monthly Review Volume Trends.
- **Interactive Filtering**: Search reviews content via keyword, filter by rating and sentiment, or filter by specific date ranges.
- **Export Capabilities**: Instantly download filtered reviews in structured **CSV** or **JSON** formats.
- **Sentiment Analysis**: Automatic sentiment scoring (Positive, Neutral, Negative) computed on the fly using Python's TextBlob library.

---

## Getting Started

### Prerequisites

- Python 3.13+
- Node.js 18+ (with npm)

---

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

### Running in Production Mode (Recommended)

FastAPI can serve the compiled React assets statically, running the entire application on a **single port (8000)**.

#### 1. Build the Frontend
```bash
cd frontend
npm run build
```

#### 2. Run the FastAPI Server
```bash
cd backend
.venv/bin/uvicorn app.main:app --port 8000
```

Open your browser to [http://localhost:8000](http://localhost:8000).

---

## Project Structure

```
milestones/
  ├── backend/               # FastAPI + Scrapers + Python Tests
  │     ├── app/
  │     │    ├── scrapers/   # Play Store and App Store scrapers
  │     │    ├── routers/    # API routes (apps, reviews, jobs)
  │     │    ├── db.py       # SQLite database logic
  │     │    ├── main.py     # Application entrypoint & static serving
  │     │    └── jobs.py     # Background workers
  │     └── tests/           # Pytest unit tests (37 tests)
  ├── frontend/              # Vite + React (SPA) + Vitest
  │     ├── src/
  │     │    ├── pages/      # SearchPage and DashboardPage
  │     │    └── __tests__/  # Frontend component & logic tests
  │     └── dist/            # Built production static assets
  ├── docs/                  # Specs and architecture plans
  └── README.md              # Setup guide
```

---

## Running Tests

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
