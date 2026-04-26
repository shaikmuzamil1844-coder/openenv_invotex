"""FastAPI app entrypoint for the OpenEnv Invotex environment.

Team Invotex — Muzamil Shaik
Meta x PyTorch x HuggingFace OpenEnv Hackathon 2026
"""

# Import domains FIRST so they register with DomainRegistry
try:
    from openenv_invotex import domains  # noqa: F401
except ImportError:
    import domains  # noqa: F401

import os
from typing import Any, Optional

from fastapi import Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:
    raise ImportError(
        "openenv-core is required. Install with: pip install 'openenv-core[core]>=0.2.1'"
    ) from e

try:
    from openenv_invotex.models import EnvAction, EnvObservation
    from openenv_invotex.server.environment import MultiDomainEnvironment
    from openenv_invotex.server.domain_registry import DomainRegistry
    from openenv_invotex.server.utils.db import engine
    from openenv_invotex.server.utils.metrics import get_metrics_response
except ImportError:
    try:
        from ..models import EnvAction, EnvObservation
        from .environment import MultiDomainEnvironment
        from .domain_registry import DomainRegistry
        from .utils.db import engine
        from .utils.metrics import get_metrics_response
    except ImportError:
        from models import EnvAction, EnvObservation
        from server.environment import MultiDomainEnvironment
        from server.domain_registry import DomainRegistry
        from server.utils.db import engine
        from server.utils.metrics import get_metrics_response


class ResetRequest(BaseModel):
    """Reset request body that can include an optional task_id."""
    task_id: Optional[str] = None


domain_name = os.getenv("DOMAIN", "email_triage").strip()

# Pre-warm domain tables on startup
_startup_domain_cls = DomainRegistry.get(domain_name)
if _startup_domain_cls:
    _startup_domain = _startup_domain_cls()
    _startup_domain.create_tables(engine)
else:
    _startup_domain = None


def _require_domain_cls() -> type:
    domain_cls = DomainRegistry.get(domain_name)
    if domain_cls is None:
        raise RuntimeError(
            f"Domain '{domain_name}' is not registered. "
            f"Available domains: {DomainRegistry.list_domains()}."
        )
    return domain_cls


def _create_app() -> Any:
    """Build the FastAPI app with OpenEnv wiring."""
    return create_app(
        MultiDomainEnvironment,
        EnvAction,
        EnvObservation,
        env_name="invotex_env",
        max_concurrent_envs=1,
    )


app = _create_app()
# Trust HF's reverse proxy so redirects use https://
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")


@app.get("/tasks")
def get_tasks() -> dict[str, Any]:
    domain_cls = _require_domain_cls()
    domain = domain_cls()
    return {
        "domain": domain_name,
        "available_domains": DomainRegistry.list_domains(),
        "tasks": domain.get_tasks(),
        "action_schema": EnvAction.model_json_schema(),
    }


@app.post("/baseline")
def run_baseline() -> Response:
    try:
        try:
            from openenv_invotex.baseline import run_baseline_all
        except ImportError:
            from baseline import run_baseline_all
        result = run_baseline_all(domain_name)
        return JSONResponse(content=result)
    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": str(exc)})


@app.post("/grader")
def grade_trajectory(payload: dict[str, Any]) -> dict[str, Any]:
    trajectory = payload.get("trajectory", [])
    domain_cls = _require_domain_cls()
    domain = domain_cls()
    graders = domain.get_graders()
    results: list[dict[str, Any]] = []
    total_score = 0.0
    for grader in graders:
        try:
            report = grader.grade(trajectory, None)
            score = float(report.get("score", 0.0))
        except Exception as exc:
            report = {"score": 0.0, "success": False, "feedback": str(exc)}
            score = 0.0
        results.append(report)
        total_score += score
    final_score = total_score / len(results) if results else 0.0
    return {"results": results, "final_score": final_score}


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "team": "Invotex",
        "author": "Muzamil Shaik",
        "domain": domain_name,
        "registered_domains": DomainRegistry.list_domains(),
    }


@app.get("/metrics")
def metrics() -> Response:
    payload, content_type = get_metrics_response()
    return Response(content=payload, media_type=content_type)


def main() -> None:
    """Entry point for running the server."""
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=7860)
    args = parser.parse_args()

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
