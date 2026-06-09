#  Copyright (c) 2024-2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

"""
Wrench job lifecycle notification helpers.

Three functions cover the full job lifecycle:
  job_register  — called when a job starts, returns a job_id
  job_update    — called during progress (optional, rate-limited to 1/s per job)
  job_close     — called when a job finishes (success or failure)

All functions are fire-and-forget on failure: they never raise, log warnings
on any error, and return None / False on failure. job_register returns the
job_id string on success or None on failure; callers should skip update/close
if job_id is None.

Secret resolution uses the same priority as slack_post:
  1. explicit service_secret param
  2. WRENCH_SERVICE_SECRET env var
  3. WRENCH_SERVICE_SECRET_ARN env var (auto-derived convention)
  4. explicit secret_arn param
"""

import os
from typing import Any, Optional

import requests

from .. import logger
from ._secret import resolve_secret


def job_register(
    workspace_id: str,
    message: str,
    source: str,
    *,
    service_name: Optional[str] = None,
    processor_name: Optional[str] = None,
    reference: Optional[str] = None,
    base_url: Optional[str] = None,
    service_secret: Optional[str] = None,
    secret_env_var: str = "WRENCH_SERVICE_SECRET",
    secret_arn: Optional[str] = None,
    boto_client: Optional[Any] = None,
    timeout: int = 10,
) -> Optional[str]:
    """
    Register a job with the Wrench notification system.

    Call once when the job begins. Store the returned job_id and pass it to
    job_update and job_close. Returns None on any failure — callers should
    skip update/close if job_id is None.

    Parameters
    ----------
    workspace_id : str
        The workspace (client) UUID the job is running for.
    message : str
        Human-readable job description shown to the user.
    source : str
        Service identifier, e.g. "elt", "featureforge", "lead_score".
    service_name : str, optional
        Internal service name. Defaults to source.
    processor_name : str, optional
        Internal processor name. Defaults to source.
    reference : str, optional
        External reference key. Defaults to workspace_id.

    Returns
    -------
    str or None
        The job_id UUID string on success, None on failure.
    """
    resolved_secret = resolve_secret(value=service_secret, env_var=secret_env_var, arn=secret_arn, boto_client=boto_client)
    if not resolved_secret:
        logger.warning("job_register: no service secret available — job not registered")
        return None

    if base_url is None:
        base_url = os.environ.get("WRENCH_API_BASE_URL", "https://api.v2.wrench.ai")

    payload = {
        "workspace_id": str(workspace_id),
        "message": message,
        "source": source,
    }
    if service_name is not None:
        payload["service_name"] = service_name
    if processor_name is not None:
        payload["processor_name"] = processor_name
    if reference is not None:
        payload["reference"] = reference

    try:
        response = requests.post(
            f"{base_url}/events/jobs/internal/register",
            json=payload,
            headers={"x-api-secret": resolved_secret, "Content-Type": "application/json"},
            timeout=timeout,
        )
        if response.ok:
            data = response.json()
            if not isinstance(data, dict):
                logger.warning(
                    f"job_register: response OK but body is not a JSON object "
                    f"(got {type(data).__name__})"
                )
                return None
            inner = data.get("data")
            job_id = inner.get("job_id") if isinstance(inner, dict) else data.get("job_id")
            if job_id:
                return str(job_id)
            logger.warning("job_register: response OK but no job_id in body")
            return None
        logger.warning(f"job_register: API returned {response.status_code}: {response.text[:200]}")
        return None
    except requests.RequestException as exc:
        logger.warning(f"job_register: request failed: {exc}")
        return None
    except Exception as exc:
        logger.warning(f"job_register: unexpected error: {exc}")
        return None


def job_update(
    job_id: Optional[str],
    progress: int,
    description: Optional[str] = None,
    *,
    workspace_id: Optional[str] = None,
    base_url: Optional[str] = None,
    service_secret: Optional[str] = None,
    secret_env_var: str = "WRENCH_SERVICE_SECRET",
    secret_arn: Optional[str] = None,
    boto_client: Optional[Any] = None,
    timeout: int = 10,
) -> bool:
    """
    Update job progress. Rate-limited to 1 call/second per job_id server-side.

    Parameters
    ----------
    job_id : str
        The job_id returned by job_register.
    progress : int
        Progress percentage 0–100.
    description : str, optional
        Human-readable progress label shown alongside the percentage.

    Returns
    -------
    bool
        True on success, False on any failure.
    """
    if not job_id:
        return False

    resolved_secret = resolve_secret(value=service_secret, env_var=secret_env_var, arn=secret_arn, boto_client=boto_client)
    if not resolved_secret:
        logger.warning("job_update: no service secret available — progress not sent")
        return False

    if base_url is None:
        base_url = os.environ.get("WRENCH_API_BASE_URL", "https://api.v2.wrench.ai")

    payload: dict = {"job_id": str(job_id), "progress": max(0, min(100, progress))}
    if description is not None:
        payload["progress_description"] = description
    if workspace_id is not None:
        payload["workspace_id"] = str(workspace_id)

    try:
        response = requests.patch(
            f"{base_url}/events/jobs/internal/update",
            json=payload,
            headers={"x-api-secret": resolved_secret, "Content-Type": "application/json"},
            timeout=timeout,
        )
        if response.ok or response.status_code == 429:  # 429 = rate limited, not an error
            return True
        logger.warning(f"job_update: API returned {response.status_code}: {response.text[:200]}")
        return False
    except requests.RequestException as exc:
        logger.warning(f"job_update: request failed: {exc}")
        return False
    except Exception as exc:
        logger.warning(f"job_update: unexpected error: {exc}")
        return False


def job_close(
    job_id: Optional[str],
    workspace_id: str,
    status_code: int,
    message: str,
    source: str,
    *,
    notify: bool = True,
    base_url: Optional[str] = None,
    service_secret: Optional[str] = None,
    secret_env_var: str = "WRENCH_SERVICE_SECRET",
    secret_arn: Optional[str] = None,
    boto_client: Optional[Any] = None,
    timeout: int = 10,
) -> bool:
    """
    Close a job. Call once when the job finishes — success, error, or cancelled.

    Parameters
    ----------
    job_id : str
        The job_id returned by job_register.
    workspace_id : str
        The workspace (client) UUID.
    status_code : int
        HTTP-style status: 200 (success), 500 (error), 499 (cancelled).
    message : str
        Completion message shown to the user.
    source : str
        Same source string used in job_register.
    notify : bool
        Whether to create a user-visible notification. Default True.

    Returns
    -------
    bool
        True on success, False on any failure.
    """
    if not job_id:
        return False

    resolved_secret = resolve_secret(value=service_secret, env_var=secret_env_var, arn=secret_arn, boto_client=boto_client)
    if not resolved_secret:
        logger.warning("job_close: no service secret available — job not closed")
        return False

    if base_url is None:
        base_url = os.environ.get("WRENCH_API_BASE_URL", "https://api.v2.wrench.ai")

    payload = {
        "job_id": str(job_id),
        "workspace_id": str(workspace_id),
        "status_code": status_code,
        "message": message,
        "source": source,
        "notify": notify,
    }

    try:
        response = requests.post(
            f"{base_url}/events/jobs/internal/close",
            json=payload,
            headers={"x-api-secret": resolved_secret, "Content-Type": "application/json"},
            timeout=timeout,
        )
        if response.ok:
            return True
        logger.warning(f"job_close: API returned {response.status_code}: {response.text[:200]}")
        return False
    except requests.RequestException as exc:
        logger.warning(f"job_close: request failed: {exc}")
        return False
    except Exception as exc:
        logger.warning(f"job_close: unexpected error: {exc}")
        return False
