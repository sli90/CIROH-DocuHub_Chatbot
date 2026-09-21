# Image for the offline ingestion / corpus-migration Fargate task
# (AWS Migration Plan, Section 3.2: "Notebook-driven scraper/populate
# scripts -> Scheduled/on-demand ECS Fargate task. Same scripts,
# containerized, runs only when triggered; no always-on server for a job
# that runs occasionally.").
#
# Built from the repo root: docker build -f backend/ingestion.Dockerfile .
# (infra/stacks/ingestion_stack.py does this automatically via
# ecs.ContainerImage.from_asset).
#
# No fixed CMD/ENTRYPOINT: the task definition's `command` is set per
# invocation (ECS RunTask `overrides`), e.g.:
#   ["python", "database/migrate_to_bedrock.py", "--validate"]
# The one-time corpus re-embed (backend/database/migrate_to_bedrock.py) is
# ready to run today; the day-to-day scraper/populate pipeline
# (PopulateDB.ipynb, GitHub_CodeRepos.ipynb, HydroShare_Datasets.ipynb) is
# still notebook-driven as of this branch (README, "In Progress / Planned"),
# so pick this image up for that once those are converted to scripts -
# nothing here is specific to the migration script.
FROM public.ecr.aws/docker/library/python:3.12-slim

WORKDIR /app/backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

ENTRYPOINT ["python"]
