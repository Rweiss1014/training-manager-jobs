# Project Status

## Live Deployment
- **URL**: https://training-manager-jobs.onrender.com/
- **Platform**: Render (Blueprint deployment)
- **Status**: WORKING - Just pushed Flask update, Render is rebuilding

## Services on Render
1. **training-manager-jobs** - Flask web app (was Streamlit, now Flask + Gunicorn)
2. **job-scraper** - Cron job (runs daily at 8 AM UTC / 3 AM EST)
3. **training-jobs-db** - PostgreSQL database (free tier)

## GitHub Repo
- https://github.com/Rweiss1014/training-manager-jobs

## Tech Stack
- **Frontend**: Flask + Jinja2 templates + custom CSS (switched from Streamlit)
- **Backend**: Python + SQLAlchemy
- **Database**: PostgreSQL (Render) / SQLite (local dev)
- **Scraper**: python-jobspy (Indeed + LinkedIn)
- **Deployment**: Gunicorn on Render

## Key Files
- `web.py` - Flask app with routes (/, /jobs)
- `templates/` - HTML templates (base.html, home.html, jobs.html)
- `static/css/style.css` - All styling
- `scraper.py` - Job scraper (runs via cron)
- `database.py` - SQLAlchemy models and DB connection
- `render.yaml` - Render deployment config

## Scraper Details
- 5 search terms (L&D, Instructional Designer, Corporate Trainer, Sales Enablement, Talent Development)
- 46 US locations
- Filters: L&D role validator, Enablement bouncer, duplicate detection
- Lookback: 30 days
- Schedule: Daily at 8 AM UTC (3 AM EST)

## Recent Changes (Latest Session)
1. Switched from Streamlit to Flask for better UI control
2. Created professional landing page matching L&D Exchange design:
   - Stats row (Active Jobs, Companies, Remote, 100% L&D Focused)
   - "Browse by L&D Specialty" section with 8 category cards
   - Two-column value proposition cards
   - Professional footer
3. Created jobs listing page with:
   - Filter sidebar (search, level, location)
   - Job cards with company, salary, location, level
   - Quick stats panel
4. Added SQLite fallback for local development
5. Updated render.yaml to use gunicorn instead of streamlit

## Where We Left Off
- Flask app pushed to GitHub (commit 9a6a118)
- Render should auto-deploy the new Flask version
- User should check https://training-manager-jobs.onrender.com/ after rebuild completes
- Local testing available at http://127.0.0.1:5000

## TODO / Future Improvements
- [ ] Fine-tune CSS to more closely match L&D Exchange screenshots (user said design doesn't look exactly like the reference)
- [ ] Add click-through on specialty cards to filter jobs
- [ ] Consider adding job detail pages
- [ ] Add email alerts feature
