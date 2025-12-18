# Django on Workers

This template provides a starting point for running a Django application on Cloudflare Workers, utilizing Cloudflare D1 for serverless SQL database and R2 for media files storage.

[![Deploy to Cloudflare](https://deploy.workers.cloudflare.com/button)](https://deploy.workers.cloudflare.com/?url=https://github.com/G4brym/django-on-workers/tree/main)

## Overview

This template is pre-configured to:
- Use `django-cf` to bridge Django with Cloudflare's environment.
- Employ Cloudflare D1 as the primary data store through the `django_cf.db.backends.d1` database engine.
- Use Cloudflare R2 for object storage and media file management through the `django_cf.storage.R2Storage` backend.
- Include a basic Django project structure within the `src/` directory.
- Provide example worker entrypoint (`src/index.py`).

## Project Structure

```
template-root/
 |-> src/
 |    |-> manage.py             # Django management script
 |    |-> index.py              # Cloudflare Worker entrypoint
 |    |-> app/                  # Your Django project (rename as needed)
 |    |    |-> settings.py       # Django settings, configured for D1, R2 and others
 |    |    |-> urls.py           # Django URLs, includes management endpoints
 |    |    |-> wsgi.py           # WSGI application
 |    |-> your_django_apps/     # Add your Django apps here
 |-> staticfiles/              # Collected static files (after build)
 |-> .gitignore
 |-> package.json              # For Node.js dependencies like wrangler
 |-> uv.lock                   # Python dependencies lock file
 |-> pyproject.toml            # Python project configuration
 |-> wrangler.jsonc            # Wrangler configuration
```

## Setup and Deployment

1.  **Install Dependencies:**
    Ensure you have Node.js, npm, and Python installed. Then:
    
    ```bash
    # Install Node.js dependencies
    npm install
    
    # Install Python dependencies
    uv sync
    ```
    
    If you don't have `uv` installed, install it first:
    ```bash
    pip install uv
    ```

2.  **Configure `wrangler.jsonc`:**
    Review and update `wrangler.jsonc` for your project. Key sections:
    *   `name`: Your worker's name.
    *   `compatibility_date`: Keep this up-to-date.
    *   `d1_databases`:
        *   `binding`: The name used to access the D1 database in your worker (e.g., "DB").
        *   `database_name`: The name of your D1 database in the Cloudflare dashboard.
        *   `database_id`: The ID of your D1 database.

    Example `d1_databases` configuration in `wrangler.jsonc`:
    ```jsonc
    {
      "d1_databases": [
        {
          "binding": "DB",
          "database_name": "my-django-db",
          "database_id": "your-d1-database-id-here"
        }
      ]
    }
    ```

3.  **Django Settings (`src/app/settings.py`):**
    The template should be configured to use D1 binding:
    ```python
    # src/app/settings.py
    DATABASES = {
        'default': {
            'ENGINE': 'django_cf.db.backends.d1',
            # This name 'DB' must match the 'binding' in your wrangler.jsonc d1_databases section
            'CLOUDFLARE_BINDING': 'DB',
        }
    }
    ```

4.  **Worker Entrypoint (`src/index.py`):**
    This file contains the main worker handler for your Django application.
    ```python
    from workers import WorkerEntrypoint
    from django_cf import DjangoCF
    from app.wsgi import application

    class Default(DjangoCF, WorkerEntrypoint):
        async def get_app(self):
            return application
    ```

5.  **Run Development Server:**
    ```bash
    npm run dev
    ```
    This starts the local development server using Wrangler.

6.  **Deploy to Cloudflare:**
    ```bash
    npm run deploy
    ```
    This command installs system dependencies and deploys your worker to Cloudflare.

## R2 Storage Configuration

This template includes support for Cloudflare R2 object storage for handling file uploads and media files.

### Setup R2 Storage

1.  **Configure `wrangler.jsonc`:**
    Add your R2 bucket binding:
    ```jsonc
    {
      "r2_buckets": [
        {
          "binding": "BUCKET",
          "bucket_name": "my-django-bucket"
        }
      ]
    }
    ```

2.  **Django Settings (`src/app/settings.py`):**
    Configure the R2 storage backend:
    ```python
    MEDIA_URL = 'https://pub-xxxxx.r2.dev/'
    
    STORAGES = {
        "default": {
            "BACKEND": "django_cf.storage.R2Storage",
            "OPTIONS": {
                "binding": "BUCKET",
                "location": "media",
                "allow_overwrite": False,
            }
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
    ```

3.  **Usage in Django:**
    ```python
    from django.core.files.base import ContentFile
    from django.core.files.storage import default_storage
    
    # Save a file
    content = ContentFile(b"Hello, R2!")
    path = default_storage.save("hello.txt", content)
    
    # Read a file
    with default_storage.open("hello.txt", "rb") as f:
        content = f.read()
    
    # Check if file exists
    exists = default_storage.exists("hello.txt")
    
    # Delete a file
    default_storage.delete("hello.txt")
    ```

### R2 Storage Features

- **Serverless Object Storage**: Store files in Cloudflare's globally distributed object storage.
- **S3-Compatible API**: R2 uses an S3-compatible API accessible through Workers bindings.
- **No Egress Fees**: R2 has no egress fees, making it cost-effective for serving files.
- **Integrated with Workers**: Direct access to R2 buckets through Worker bindings.

For more details on R2 storage configuration and access control options, refer to the [django-cf documentation](https://github.com/G4brym/django-cf#cloudflare-r2-storage).

## Running Management Commands

For D1, you can use the special management endpoints provided in the template:

*   **`/__run_migrations__/`**: Triggers the `migrate` command.
*   **`/__create_admin__/`**: Creates a superuser (username: 'admin', password: 'password').

These endpoints are defined in `src/app/urls.py` and are protected by `user_passes_test(is_superuser)`. This means you must first create an admin user and be logged in as that user to access these endpoints.

**Initial Admin User Creation:**
For the very first admin user creation, you might need to temporarily remove the `@user_passes_test(is_superuser)` decorator from `create_admin_view` in `src/app/urls.py`, deploy, access `/__create_admin__/`, and then reinstate the decorator and redeploy. Alternatively, modify the `create_admin_view` to accept a secure token or other mechanism for the initial setup if direct unauthenticated access is undesirable.

**Accessing the Endpoints:**
Once deployed and an admin user exists (and you are logged in as them):
- Visit `https://your-worker-url.com/__run_migrations__/` to apply migrations.
- Visit `https://your-worker-url.com/__create_admin__/` to create the admin user if needed.

Check the JSON response in your browser to see the status of the command.

## Development Notes

*   **D1 Limitations:**
    *   **Transactions are disabled** for D1. Every query is committed immediately. This is a fundamental aspect of D1.
    *   The D1 backend has some limitations compared to traditional SQLite or other SQL databases. Many advanced ORM features or direct SQL functions (especially those used in Django Admin) might not be fully supported. Refer to the `django-cf` README and official Cloudflare D1 documentation.
    *   Django Admin functionality might be limited.
*   **Local Testing with D1:**
    *   Wrangler allows local development and can simulate D1 access. `npx wrangler dev --remote` can connect to your actual D1 database for more accurate testing.
*   **Security:**
    *   The management command endpoints are protected by Django's `user_passes_test(is_superuser)`. Ensure they are properly secured before deploying to production.
    *   Protect your Cloudflare credentials and API tokens.

---
*For more details on `django-cf` features and configurations, refer to the main [django-cf GitHub repository](https://github.com/G4brym/django-cf).*
