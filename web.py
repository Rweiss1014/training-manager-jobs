"""
L&D Job Board - Flask Web Application
"""

from flask import Flask, render_template, request
from database import get_session, Job
from datetime import date

app = Flask(__name__)


def get_stats():
    """Get job statistics for the landing page."""
    with get_session() as session:
        total_jobs = session.query(Job).count()
        companies = session.query(Job.company).distinct().count()
        remote_jobs = session.query(Job).filter(
            Job.location.ilike('%remote%')
        ).count()

        # Jobs added today
        today = date.today()
        new_today = session.query(Job).filter(
            Job.created_at >= today
        ).count()

        return {
            'total_jobs': total_jobs,
            'companies': companies,
            'remote_jobs': remote_jobs,
            'new_today': new_today
        }


def get_specialty_counts():
    """Count jobs by L&D specialty."""
    specialties = {
        "Instructional Design": ["instructional design", "curriculum design"],
        "E-Learning Development": ["e-learning", "elearning", "digital learning"],
        "Training & Facilitation": ["training", "facilitator", "trainer"],
        "Learning Management": ["learning management", "lms"],
        "Curriculum Development": ["curriculum", "course design"],
        "Corporate Training": ["corporate training", "corporate learning"],
        "Learning Technology": ["learning tech", "edtech"],
        "Talent Development": ["talent develop", "l&d manager", "learning director"]
    }

    counts = {}
    with get_session() as session:
        all_jobs = session.query(Job).all()

        for specialty, keywords in specialties.items():
            count = 0
            for job in all_jobs:
                title = (job.title or '').lower()
                desc = (job.description or '').lower()
                if any(kw in title or kw in desc for kw in keywords):
                    count += 1
            counts[specialty] = count

    return counts


def get_jobs(filters=None):
    """Get filtered job listings."""
    with get_session() as session:
        query = session.query(Job)

        if filters:
            if filters.get('search'):
                search = f"%{filters['search']}%"
                query = query.filter(
                    (Job.title.ilike(search)) | (Job.company.ilike(search))
                )
            if filters.get('level'):
                query = query.filter(Job.level == filters['level'])
            if filters.get('location'):
                loc = f"%{filters['location']}%"
                query = query.filter(Job.location.ilike(loc))

        # Order by newest first
        query = query.order_by(Job.created_at.desc())

        jobs = query.all()

        # Convert to dicts to avoid detached session issues
        return [{
            'id': j.id,
            'title': j.title,
            'company': j.company,
            'salary': j.salary,
            'location': j.location,
            'level': j.level,
            'job_url': j.job_url,
            'date_posted': j.date_posted,
            'created_at': j.created_at
        } for j in jobs]


@app.route('/')
def home():
    """Landing page."""
    stats = get_stats()
    specialty_counts = get_specialty_counts()

    specialties = [
        {"name": "Instructional Design", "color": "blue", "count": specialty_counts.get("Instructional Design", 0)},
        {"name": "E-Learning Development", "color": "purple", "count": specialty_counts.get("E-Learning Development", 0)},
        {"name": "Training & Facilitation", "color": "green", "count": specialty_counts.get("Training & Facilitation", 0)},
        {"name": "Learning Management", "color": "orange", "count": specialty_counts.get("Learning Management", 0)},
        {"name": "Curriculum Development", "color": "teal", "count": specialty_counts.get("Curriculum Development", 0)},
        {"name": "Corporate Training", "color": "pink", "count": specialty_counts.get("Corporate Training", 0)},
        {"name": "Learning Technology", "color": "blue", "count": specialty_counts.get("Learning Technology", 0)},
        {"name": "Talent Development", "color": "purple", "count": specialty_counts.get("Talent Development", 0)},
    ]

    return render_template('home.html', stats=stats, specialties=specialties)


@app.route('/jobs')
def jobs():
    """Job listings page."""
    filters = {
        'search': request.args.get('search', ''),
        'level': request.args.get('level', ''),
        'location': request.args.get('location', '')
    }

    jobs_list = get_jobs(filters if any(filters.values()) else None)
    stats = get_stats()

    # Get unique locations for filter dropdown
    with get_session() as session:
        locations = [loc[0] for loc in session.query(Job.location).distinct().all() if loc[0]]
        locations = sorted(set(locations))

    return render_template('jobs.html',
                         jobs=jobs_list,
                         stats=stats,
                         filters=filters,
                         locations=locations)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
