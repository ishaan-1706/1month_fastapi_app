# 1month_fastapi_app

A FastAPI application with PostgreSQL, JWT authentication, Alembic migrations, testing, and Docker Compose setup.

---

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/your-org/1month_fastapi_app.git
cd 1month_fastapi_app

# 2. Copy environment template
cp .env.example .env

# 3. Run migrations
alembic upgrade head

# 4. Start the app
uvicorn fastapi_postgres_app.main:app --reload

# 5. Open docs
http://localhost:8000/docs
```
## Prerequisites

- Python 3.10+

- PostgreSQL 12+

- Docker & Docker Compose (for containerized setup)

- Git

## Environment Setup
This project uses two environment files to separate local and Docker workflows.

### Local Development (.env)
```
# .env.docker

JWT_SECRET=your_jwt_secret
JWT_ALGORITHM=HS256

# PostgreSQL (inside Docker network)
DATABASE_URL=postgresql://postgres:password@db:5432/fastapi_db
```
### Docker Compose (.env.docker)
```
# .env.docker

JWT_SECRET=your_jwt_secret
JWT_ALGORITHM=HS256

# PostgreSQL (inside Docker network)
DATABASE_URL=postgresql://postgres:password@db:5432/fastapi_db
```
## Installation
```
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.\.venv\Scripts\activate    # Windows PowerShell

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy .env.example to .env and update values
cp .env.example .env
```
## Database Migrations
```
# Initialize Alembic (already done)
alembic init alembic

# Create a new revision when models change
alembic revision --autogenerate -m "Describe change"

# Apply migrations
alembic upgrade head
```
## Running Locally
```
uvicorn fastapi_postgres_app.main:app --reload
```
Access:

   - Swagger UI → http://localhost:8000/docs

   - OpenAPI JSON → http://localhost:8000/openapi.json
## Docker Compose
### Build & Run
```
# in docker-compose.yml
env_file:
  - .env.docker
```
```# Build and start containers
docker-compose up --build
```
Visit:

  - Swagger UI → http://localhost:8000/docs

  - Database GUI → Docker Desktop (optional)
### Tear Down
```
# Stop containers
docker-compose down

# Remove volumes (reset DB)
docker-compose down -v
```
## Testing
```# Run the full test suite
pytest -q

# For detailed output
pytest
```
## Seeding the Database
```
## Seeding the Database

An optional convenience script to populate sample items.

1. Ensure your environment is configured (`.env` or inside Docker).  
2. Run locally:
   python seed.py

# Or inside Docker
docker-compose exec web python seed.py

```
Then verify:
```
curl http://localhost:8000/items
```
## Contributing
1. Fork the repository

2. Create a feature branch

3. Commit your changes

4. Open a pull request

Update .env.example and add migrations when you modify models.
## License
This project is licensed under the MIT License.