run:
\tuvicorn app.main:app --reload

compose-up:
\tdocker compose -f docker-compose.dev.yml up --build

compose-down:
\tdocker compose -f docker-compose.dev.yml down
