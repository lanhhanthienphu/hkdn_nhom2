# Helpdesk System

A Django project for a helpdesk system. Apps currently included: `accounts`, `kb`, and `tickets`.

## Requirements

- Python compatible with the Django version in `requirements.txt`
- pip

## Run locally (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py manage.py check
py manage.py migrate
py manage.py runserver
```

Open http://127.0.0.1:8000/ . The Django admin is at http://127.0.0.1:8000/admin/ .

## Notes

- The local SQLite database and virtual environment are intentionally not included in Git.
- Configure `DJANGO_SECRET_KEY` through an environment variable for any non-local deployment. The fallback key is for local development only.
- The project currently contains the initial Django app scaffolding; models, views, and app routes may need to be implemented as the project develops.
