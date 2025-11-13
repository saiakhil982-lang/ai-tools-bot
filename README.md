# 🤖 AI Tools Chatbot

A beginner-friendly Streamlit chatbot that teaches you how to discover the newest AI tools for different use cases (finance, customer support, content creation, devtools, and more). The project uses only free services, refreshes automatically every day, and works even if you skip every API key.

---

## 🎯 What You Get
- Streamlit chat experience that shows AI tool recommendations and clear summaries.
- Free Product Hunt + GitHub Trending scrapers (run daily with GitHub Actions).
- Email alerts powered by a free Gmail App Password (optional).
- CSV fallback so everything still works with zero keys.
- Optional Hugging Face `distilgpt2` summarizer (works if `transformers` + `torch` are installed; otherwise a simple deterministic summary is used).

---

## 🧰 Project Structure
```
ai-tools-chatbot/
├── streamlit_app.py              # Streamlit UI, tool fetching, summarizer
├── data/
│   ├── sample_ai_tools.csv       # Always available fallback data (8 tools)
│   └── tools.csv                 # Auto-generated daily by GitHub Actions
├── scrapers/
│   ├── scrape_producthunt.py     # Product Hunt API scraper (optional)
│   ├── scrape_github_trending.py # GitHub Trending scraper (free HTML fetch)
│   ├── merge_and_write.py        # Dedup, sort, write tools.csv, save new list
│   └── alert_and_commit.py       # Email alerts + git commit/push
├── .github/workflows/daily_scrape.yml # Daily automation pipeline
├── .streamlit/secrets.toml.example   # Sample Streamlit secrets file
├── requirements.txt              # Dependencies (transformers optional)
├── README.md                     # Beginner guide (this file)
├── DEPLOYMENT.md                 # Quick reference deployment doc
└── LICENSE                       # MIT License
```

---

## ✅ Prerequisites (all free)
- GitHub account (free) — used for hosting code and running GitHub Actions.
- Google account (free) — used for Gmail App Password alerts (optional).
- Product Hunt account (free) — only if you want real Product Hunt API data.
- Streamlit Community Cloud account (free) — runs the chatbot in the cloud.

Everything still works with just the sample CSV if you skip the optional services.

---

## 🧭 Beginner Step-by-Step Guide

### 1. Create Your GitHub Repository & Upload Files
1. **Get a copy of this project**
   - In Cursor (or your editor), export/download the project folder, or clone this repo locally.
2. **Create a new GitHub repository**
   - Visit [https://github.com/new](https://github.com/new)
   - Repository name: `ai-tools-bot-yourusername`
   - Keep it **Public** (required for free Streamlit hosting)
   - Do **not** initialize with README or anything else.
3. **Upload the project files** *(two options)*
   - **Automatic (Cursor Git integration)**: Use Cursor's "Publish" or "Push" command if it is available and already authenticated with GitHub.
   - **Manual (command line)**:
     ```bash
     cd /path/to/ai-tools-chatbot
     git init
     git remote add origin https://github.com/<your-username>/ai-tools-bot-<yourusername>.git
     git add .
     git commit -m "Initial commit"
     git branch -M main
     git push -u origin main
     ```
4. Confirm the repository now shows all files on GitHub.

### 2. (Optional) Product Hunt API Key
The app works without this step. If you want live Product Hunt data:
1. Create a free Product Hunt account: [https://www.producthunt.com/](https://www.producthunt.com/)
2. Visit the Product Hunt API dashboard: [https://api.producthunt.com/v2/oauth/applications](https://api.producthunt.com/v2/oauth/applications)
3. Click **“Create an Application”** → fill basic info (name, description can be simple)
4. Copy the **API Key** (a long string). You will store it as a GitHub Secret later.
5. If you hit rate limits, the app falls back to the CSV automatically.

### 3. Create a Free Gmail App Password (for email alerts)
Email alerts are optional but recommended. Make sure you have 2-Step Verification enabled on your Google account first.
1. Go to [https://myaccount.google.com/](https://myaccount.google.com/)
2. In the left menu choose **Security**.
3. Under **"Signing in to Google"**, make sure **2-Step Verification** is ON. If not, click it and follow the prompts to enable it.
4. Back under **Security**, click **App passwords** (only visible after 2-Step is enabled).
5. When prompted:
   - Select **App**: `Mail`
   - Select **Device**: `Other (Custom name)` and enter `GitHub Actions`
6. Click **Generate**. Google shows a 16-character password (no spaces). Copy it and keep it safe — you cannot see it again later.

### 4. Add GitHub Secrets (so GitHub Actions can use them)
1. Open your GitHub repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**.
2. Add the following secrets (copy/paste values carefully):
   - `SMTP_USER` → your Gmail address (example: `yourname@gmail.com`)
   - `SMTP_PASS` → the 16-character Gmail App Password from step 3
   - `EMAIL_TO` → email that should receive alerts (can be the same Gmail)
   - `PRODUCTHUNT_API_KEY` → Product Hunt API key (only if you completed step 2)
3. You can add more later without redeploying anything.

### 5. Deploy to Streamlit Community Cloud (free hosting)
1. Visit [https://streamlit.io/cloud](https://streamlit.io/cloud) and sign in with GitHub.
2. Click **“New app”** → choose your `ai-tools-bot-<username>` repository.
3. Set **Main file path** to `streamlit_app.py`.
4. Click **Deploy**.
5. Once the app boots, configure optional secrets:
   - In Streamlit Cloud, open the **“⋮” menu** → **Settings** → **Secrets**.
   - Paste the contents of `.streamlit/secrets.toml.example` (remove comments) and fill in your values.
   - Leave empty values if you are skipping API/email features.

### 6. Test with Beginner-Friendly Prompts
Use the chat box and try these sample prompts:
- “Show me finance tools.”
- “What AI tools help with customer support?”
- “Suggest content creation AI tools.”
- “Any developer tools for machine learning?”

While your API keys are missing, data comes from `data/sample_ai_tools.csv`. That is OK!

### 7. Troubleshooting & Common Questions
| Situation | Fix |
|-----------|-----|
| **No Product Hunt key?** | The app automatically uses `data/sample_ai_tools.csv` and any previously scraped GitHub Trending tools. No action needed.
| **Transformers install too heavy?** | Leave `transformers` and `torch` commented out in `requirements.txt`. The app will show a friendly message and use the deterministic summary template.
| **Email alerts not arriving?** | Double-check Gmail App Password, ensure 2FA is on, confirm secrets (`SMTP_USER`, `SMTP_PASS`, `EMAIL_TO`) match exactly, and read the GitHub Actions log for clear error messages.
| **GitHub Trending scraper fails?** | GitHub may change HTML structure. The daily job will log a warning but the workflow continues thanks to fallback CSV.
| **Daily workflow errors?** | Open the repo → **Actions** tab → select the failed run → read the step logs. Messages are written in plain language with suggestions.
| **Want SMS/WhatsApp alerts?** | Twilio works but may incur cost. You would add your own code/secrets — this template keeps everything 100% free and email-based by default.

---

## 🔄 How Daily Automation Works
1. **GitHub Actions** (`.github/workflows/daily_scrape.yml`) runs every day at 09:00 UTC.
2. **`scrape_producthunt.py`** adds new tools when `PRODUCTHUNT_API_KEY` is available.
3. **`scrape_github_trending.py`** gathers AI/ML repos from GitHub Trending (category `devtools`).
4. **`merge_and_write.py`** deduplicates, sorts by launch date, and stores a list of newly discovered tools in `data/new_tools.json`.
5. **`alert_and_commit.py`** sends a Gmail alert (if there are new tools + secrets configured) and commits `data/tools.csv` back to the repo using `GITHUB_TOKEN`.
6. Everything runs with free-tier services. If any scraper fails, the workflow exits gracefully so your daily job never blocks on missing keys.

---

## ⚙️ Optional: GUI Automation (n8n or Zapier)
Prefer a drag-and-drop automation experience later? Here is how to hook it up:

### n8n Webhook Flow
1. Create a free n8n cloud or self-hosted account.
2. In n8n, add a **Webhook** trigger node → set it to `POST` → copy the public webhook URL.
3. Add nodes to send email, Slack messages, etc. (n8n has Gmail, Slack, Discord integrations with free tiers).
4. In your GitHub repository, edit `.github/workflows/daily_scrape.yml` and add a final step:
   ```yaml
   - name: Call n8n webhook (optional)
     if: success()  # only run when previous steps succeeded
     run: |
       curl -X POST ${{ secrets.N8N_WEBHOOK_URL }} \
         -H "Content-Type: application/json" \
         -d @data/new_tools.json || echo "No webhook triggered"
     env:
       N8N_WEBHOOK_URL: ${{ secrets.N8N_WEBHOOK_URL }}
   ```
5. Add `N8N_WEBHOOK_URL` as a GitHub Secret. Done! The webhook receives the list of new tools as JSON.

### Zapier Webhook (similar idea)
1. Create a Zap → choose **“Webhook by Zapier”** → **Catch Hook**.
2. Copy the custom webhook URL.
3. Add the same `curl` step above (use `ZAPIER_WEBHOOK_URL` secret instead).
4. Build any follow-up Zap actions (add to Google Sheet, send Gmail, etc.).

This keeps email alerts via Gmail free while letting you expand to GUI workflows when you are ready.

---

## 📦 Requirements File Tips
`requirements.txt` keeps `transformers` and `torch` commented out. Uncomment them only if you need AI-written summaries and your environment allows larger packages. Without them, the app explains that it is using the template summarizer.

---

## 🔐 Streamlit Secrets Template
Use `.streamlit/secrets.toml.example` as your copy/paste reference. Remember: leaving values blank is fine — the code checks for environment variables and falls back to safe defaults.

---

## 🛡️ License
This project is released under the permissive [MIT License](LICENSE). You can modify it, use it commercially, and share your own forks.

---

## 🙌 Support & Contributions
- Open GitHub issues for bugs or enhancement ideas.
- Submit PRs with new scrapers, UI improvements, or tutorials.
- Share your deployed Streamlit link so others can try it!

Happy building! 🚀

