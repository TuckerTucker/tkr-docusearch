"""Project API endpoints for managing document projects.

Provides CRUD operations for projects -- logical containers
that partition the document library.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ...storage import KojiClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["projects"])

# Injected at startup by server.py
_storage_client: KojiClient | None = None


def set_storage_client(storage_client: KojiClient) -> None:
    """Set the storage client for project endpoints."""
    global _storage_client
    _storage_client = storage_client


def _require_storage() -> KojiClient:
    """Raise 503 if storage not initialized."""
    if _storage_client is None:
        raise HTTPException(503, "Storage service not available")
    return _storage_client


# ---------------------------------------------------------------------------
# Slug helper
# ---------------------------------------------------------------------------

_SLUG_UNSAFE = re.compile(r"[^a-z0-9]+")


def _slugify(name: str) -> str:
    """Convert a project name to a URL-safe slug.

    Args:
        name: Human-readable project name.

    Returns:
        Lowercase slug with hyphens (max 128 chars).
    """
    slug = _SLUG_UNSAFE.sub("-", name.lower()).strip("-")
    return slug[:128] or "project"


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------


class ProjectCreate(BaseModel):
    """Request body for creating a project."""

    name: str
    project_id: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[dict] = None


class ProjectUpdate(BaseModel):
    """Request body for updating a project."""

    name: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[dict] = None


class ProjectResponse(BaseModel):
    """Project with document count."""

    project_id: str
    name: str
    description: Optional[str] = None
    created_at: str
    metadata: Optional[dict] = None
    document_count: int = 0


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(body: ProjectCreate) -> ProjectResponse:
    """Create a new project.

    Auto-generates ``project_id`` from the name if not provided.
    """
    storage = _require_storage()

    pid = body.project_id or _slugify(body.name)

    try:
        project = storage.create_project(
            project_id=pid,
            name=body.name,
            description=body.description,
            metadata=body.metadata,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:
        if "already exists" in str(exc):
            raise HTTPException(409, f"Project {pid!r} already exists")
        logger.error(f"Failed to create project: {exc}", exc_info=True)
        raise HTTPException(500, f"Failed to create project: {exc}")

    return ProjectResponse(
        project_id=project["project_id"],
        name=project["name"],
        description=project.get("description"),
        created_at=project["created_at"],
        metadata=project.get("metadata"),
        document_count=0,
    )


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> list[ProjectResponse]:
    """List all projects with document counts."""
    storage = _require_storage()

    try:
        projects = storage.list_projects(limit=limit, offset=offset)
    except Exception as exc:
        logger.error(f"Failed to list projects: {exc}", exc_info=True)
        raise HTTPException(500, f"Failed to list projects: {exc}")

    result = []
    for p in projects:
        doc_count = storage.count_documents_in_project(p["project_id"])
        result.append(ProjectResponse(
            project_id=p["project_id"],
            name=p.get("name", p["project_id"]),
            description=p.get("description"),
            created_at=p.get("created_at", ""),
            metadata=p.get("metadata"),
            document_count=doc_count,
        ))
    return result


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str) -> ProjectResponse:
    """Get a single project by ID."""
    storage = _require_storage()

    project = storage.get_project(project_id)
    if project is None:
        raise HTTPException(404, f"Project not found: {project_id}")

    doc_count = storage.count_documents_in_project(project_id)

    return ProjectResponse(
        project_id=project["project_id"],
        name=project.get("name", project_id),
        description=project.get("description"),
        created_at=project.get("created_at", ""),
        metadata=project.get("metadata"),
        document_count=doc_count,
    )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, body: ProjectUpdate) -> ProjectResponse:
    """Update a project's name, description, or metadata."""
    storage = _require_storage()

    project = storage.get_project(project_id)
    if project is None:
        raise HTTPException(404, f"Project not found: {project_id}")

    fields: dict[str, Any] = {}
    if body.name is not None:
        fields["name"] = body.name
    if body.description is not None:
        fields["description"] = body.description
    if body.metadata is not None:
        fields["metadata"] = body.metadata

    if not fields:
        raise HTTPException(400, "No fields to update")

    try:
        storage.update_project(project_id, **fields)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:
        logger.error(f"Failed to update project: {exc}", exc_info=True)
        raise HTTPException(500, f"Failed to update project: {exc}")

    return await get_project(project_id)


@router.delete("/{project_id}")
async def delete_project(project_id: str) -> dict:
    """Delete a project and all its documents.

    The ``"default"`` project cannot be deleted.
    """
    storage = _require_storage()

    project = storage.get_project(project_id)
    if project is None:
        raise HTTPException(404, f"Project not found: {project_id}")

    try:
        deleted_count = storage.delete_project(project_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:
        logger.error(f"Failed to delete project: {exc}", exc_info=True)
        raise HTTPException(500, f"Failed to delete project: {exc}")

    return {
        "success": True,
        "project_id": project_id,
        "documents_deleted": deleted_count,
    }
