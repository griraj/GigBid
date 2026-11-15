.PHONY: dev test eval seed lint demo
dev:
	uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000
test:
	python -m pytest -q
eval:
	python -m evals.runners.compare_retrieval
	python -m evals.runners.evaluate_system
seed:
	python -c "from data.synthetic import JOBS,EVIDENCE; print(len(JOBS),'synthetic jobs;',len(EVIDENCE),'synthetic evidence items')"
lint:
	python -m compileall -q agent apps data rag mcp_servers evals
demo:
	python -c "from fastapi.testclient import TestClient; from apps.api.main import app; c=TestClient(app); print(c.get('/health').json())"
