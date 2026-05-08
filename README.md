# Social Media Data Pipeline

This is a complete data pipeline for social media intelligence. It ingests data from various social media platforms (TikTok, Instagram, X/Twitter, Facebook, YouTube, LinkedIn) using Apify actors, flattens the nested JSON data using Pandas, enriches the text with language detection, sentiment analysis, and topic classification via Claude (Anthropic), and serves the final structured data through a FastAPI application ready for Power BI consumption.

## Prerequisites
- Python 3.9+
- An [Apify](https://apify.com/) Account & API Token
- An [Anthropic](https://console.anthropic.com/) Account & API Key (for Claude 3)

---

## 1. Installation & Setup

1. **Clone or Navigate to the Directory**:
   Open a terminal and ensure you are in the project root (`sociaaltool` folder).

2. **Create a Virtual Environment**:
   It is recommended to use a virtual environment to manage dependencies.
   ```bash
   # Create a virtual environment named "venv"
   python -m venv venv

   # Activate it (Windows)
   venv\Scripts\activate

   # Activate it (Mac/Linux)
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 2. Configuration & API Keys

All configuration is handled via environment variables using a `.env` file.

1. **Create the `.env` file**:
   Copy the provided `.env.example` file and rename it to `.env`:
   ```bash
   cp .env.example .env
   ```

2. **Set up API Keys**:
   Open `.env` and fill in your keys:
   - `APIFY_API_TOKEN`: Your API token from your [Apify Account Settings](https://console.apify.com/account/integrations).
   - `ANTHROPIC_API_KEY`: Your API key from the [Anthropic Console](https://console.anthropic.com/settings/keys).

### Configuring Apify Actors
The pipeline is designed to trigger specific "Actors" on Apify. An actor is essentially a scraper for a specific website. 
In the `.env` file, you will define exactly which Apify actor to run for each platform:

| Platform | Recommended Actor ID | Where to set it in `.env` |
|----------|----------------------|---------------------------|
| **X / Twitter** | `apidojo/tweet-scraper` | `ACTOR_X_ID=apidojo/tweet-scraper` |
| **Instagram** | `apify/instagram-scraper` | `ACTOR_INSTAGRAM_ID=apify/instagram-scraper` |
| **TikTok** | `clockworks/tiktok-profile-scraper` | `ACTOR_TIKTOK_ID=clockworks/tiktok-profile-scraper` |
| **YouTube** | `streamers/youtube-scraper` | `ACTOR_YOUTUBE_ID=streamers/youtube-scraper` |
| **Facebook** | `apify/facebook-pages-scraper` | `ACTOR_FACEBOOK_ID=apify/facebook-pages-scraper` |
| **LinkedIn** | `curious_coder/linkedin-profile-scraper` | `ACTOR_LINKEDIN_ID=curious_coder/linkedin-profile-scraper` |

*Note: You can swap these with any other Apify Actor ID that meets your needs. Just change the value in your `.env` file. Be aware that different actors return differently structured data, so if you use radically different actors, you may need to update the data transformation logic in `app/services/processing_service.py`.*

---

## 3. Running the Application

Start the FastAPI application using `uvicorn`:

```bash
uvicorn app.main:app --reload
```

The API will start locally on `http://127.0.0.1:8000`.

Start the Next.js admin dashboard in a second terminal:

```bash
cd app/admin-dashboard
npm install
npm run dev
```

The admin dashboard will build and start locally on `http://127.0.0.1:3000`, then proxy `/api/*` requests to the FastAPI backend. If your API is running somewhere else, set `NEXT_PUBLIC_API_URL` before starting Next.js:

```bash
set NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
npm run dev
```

For Next.js hot reload while editing the dashboard, you can use:

```bash
npm run next-dev
```

---

## 4. Usage & Endpoints

You can explore and test all endpoints using the auto-generated Swagger UI:
👉 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

### A. Trigger Data Ingestion (`POST /api/v1/ingestion/`)
This endpoint runs the full pipeline: it triggers the Apify scraper, flattens the result, passes the text to Claude for analysis, and saves the final JSON file to the `data/processed` folder.

**Example Request payload:**
```json
{
  "platform": "tiktok",
  "targets": ["nike", "adidas"]
}
```

### B. View Processed Data for Power BI (`GET /api/v1/powerbi/data/{platform}`)
This endpoint exposes the enriched data so tools like Power BI can consume it seamlessly.
- **Path Parameter**: `{platform}` (e.g., `tiktok`, `instagram`)
- **Query Parameters**: 
  - `limit` (default 100)
  - `offset` (default 0)
  - `sentiment` (filter by positive/negative/neutral)
  - `category` (filter by topic)

### C. Dashboard Summary (`GET /api/v1/powerbi/summary/{platform}`)
Returns an aggregated summary of the data, including sentiment distribution, language distribution, and category breakdowns. Perfect for high-level dashboard visualizations.

### D. Admin Dashboard
The Next.js dashboard includes:
- Demo login.
- Platform overview metrics.
- Apify actor runs with debug and AI enrichment controls.
- Raw and processed data explorer with JSON/table views.
- File inventory.
- Backend configuration/status.
- Reports with sentiment, language, category distributions, filters, and CSV export.

---

## Data Storage Strategy
Currently, data is stored locally in the `data/` folder at the root of the project:
- `data/raw/`: Contains the exact JSON payloads returned directly from Apify.
- `data/processed/`: Contains the flattened versions, as well as the `_enriched.json` files that include Claude's AI analysis. 

*(For production, this logic in `app/services/storage_service.py` can be updated to point to an S3 bucket or a relational database).*
