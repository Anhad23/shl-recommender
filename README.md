# SHL Assessment Recommender

## Setup (do this once)

```bash
# 1. Create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your Anthropic API key
export ANTHROPIC_API_KEY=sk-ant-...   # Windows: set ANTHROPIC_API_KEY=sk-ant-...
```

## Run in order

### Step 1 — Scrape the catalog
```bash
python scraper.py
# Creates: catalog.json, catalog_raw.html
```
If the selectors are wrong, open catalog_raw.html in your browser,
right-click a product row → Inspect, find the CSS class, update scraper.py.

### Step 2 — Build the vector index
```bash
python build_index.py
# Creates: catalog.index, catalog.pkl
```

### Step 3 — Run the API locally
```bash
uvicorn main:app --reload --port 8000
```

### Step 4 — Test it
```bash
# Health check
curl http://localhost:8000/health

# Chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "I need an assessment"}]}'

# Full conversation
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hiring a Java developer who works with stakeholders"},
      {"role": "assistant", "content": "{\"reply\": \"What is the seniority level?\", \"recommendations\": [], \"end_of_conversation\": false}"},
      {"role": "user", "content": "Mid-level, around 4 years experience"}
    ]
  }'
```

## Deploy to Render (free)

1. Push this folder to a GitHub repo
2. Go to render.com → New → Web Service → connect your repo
3. Set:
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add environment variable: `ANTHROPIC_API_KEY = sk-ant-...`
5. Deploy — your URL will be `https://your-app.onrender.com`

## Files needed on the server
Make sure catalog.index and catalog.pkl are committed to your repo,
OR add a build step that runs build_index.py before starting.
