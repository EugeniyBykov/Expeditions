# Expeditions API

## Setup

Create and activate a virtual environment:

    python3 -m venv .venv
    source .venv/bin/activate

Install dependencies:

    make install

Copy environment variables:

    cp sample.env .env

Update `.env` if needed, especially `DATABASE_URL`.

## Database initial setup

Apply the initial migration to create the database schema:

    alembic upgrade head

Seed initial data:

    python3 scripts/seed_data.py

If you need to reset the database during development, run:

    make wipe-db

If you are using Docker, make sure PostgreSQL is running before applying migrations.

## Run the project

### Local

    make run

### Docker

    docker compose up --build

## Export OpenAPI schema

Generate the OpenAPI JSON schema from the application and save it to a file:

    python3 app/tools/scripts/export_openapi.py openapi.json

Notes:

- Run this command from the project root.
- The output path must end with `.json`.
- You can choose any output filename, for example `docs/openapi.json` or `openapi.json`.

## Useful commands

    make install
    make lint
    make format
    make test
    make run
    make wipe-db

## Notes

- The app uses environment variables for configuration.
- Database changes should be added through Alembic migrations.
- The initial migration only needs to be applied once for a fresh database.