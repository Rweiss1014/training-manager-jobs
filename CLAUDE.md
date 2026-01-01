# Project Status

## Live Deployment
- **URL**: https://training-manager-jobs.onrender.com/
- **Platform**: Render (Blueprint deployment)
- **Status**: WORKING

## Services on Render
1. **training-manager-jobs** - Streamlit web app
2. **job-scraper** - Cron job (runs daily at 8 AM UTC / 3 AM EST)
3. **training-jobs-db** - PostgreSQL database (free tier)

## GitHub Repo
- https://github.com/Rweiss1014/training-manager-jobs

## Tech Stack
- **Frontend**: Streamlit
- **Backend**: Python + SQLAlchemy
- **Database**: PostgreSQL (Render) / SQLite (local dev)
- **Scraper**: python-jobspy (Indeed + LinkedIn)

## Scraper Details
- 5 search terms (L&D, Instructional Designer, Corporate Trainer, Sales Enablement, Talent Development)
- 46 US locations
- Filters: L&D role validator, Enablement bouncer, duplicate detection
- Lookback: 30 days

## TODO
- [ ] Improve landing page design to match L&D Exchange style (user has reference screenshots)
