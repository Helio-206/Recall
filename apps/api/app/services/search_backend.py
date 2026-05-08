from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class SearchBackendUnavailable(Exception):
    pass


class MeiliSearchBackend:
    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def enabled(self) -> bool:
        return self.settings.search_enabled and self.settings.search_backend == "meilisearch"

    def ensure_index(self) -> None:
        if not self.enabled:
            return

        try:
            self._request(
                "POST",
                "/indexes",
                json={"uid": self.settings.search_index_uid, "primaryKey": "id"},
                tolerate_statuses={202, 400, 409},
            )
            self._request(
                "PATCH",
                f"/indexes/{self.settings.search_index_uid}/settings",
                json={
                    "searchableAttributes": [
                        "title",
                        "content",
                        "video_title",
                        "space_title",
                    ],
                    "displayedAttributes": [
                        "id",
                        "kind",
                        "user_id",
                        "video_id",
                        "video_title",
                        "space_id",
                        "space_title",
                        "timestamp",
                        "title",
                        "content",
                        "target_tab",
                        "updated_at",
                        "completed",
                    ],
                    "filterableAttributes": [
                        "user_id",
                        "kind",
                        "space_id",
                        "completed",
                    ],
                    "sortableAttributes": ["updated_at", "timestamp"],
                    "rankingRules": [
                        "words",
                        "typo",
                        "proximity",
                        "attribute",
                        "sort",
                        "exactness",
                    ],
                },
                tolerate_statuses={202},
            )
        except SearchBackendUnavailable:
            logger.warning("Search backend is unavailable during startup/index setup.")

    def search(self, *, query: str, filter_expression: str, offset: int, limit: int) -> dict[str, Any]:
        if not self.enabled:
            return {"hits": [], "estimatedTotalHits": 0}

        response = self._request(
            "POST",
            f"/indexes/{self.settings.search_index_uid}/search",
            json={
                "q": query,
                "filter": filter_expression,
                "offset": offset,
                "limit": limit,
                "attributesToHighlight": ["title", "content", "video_title", "space_title"],
                "attributesToCrop": ["content"],
                "cropLength": self.settings.search_excerpt_words,
                "showRankingScore": True,
            },
        )
        return response

    def replace_video_documents(self, *, video_id: str, documents: list[dict[str, Any]]) -> None:
        if not self.enabled:
            return

        existing = self.search(
            query="",
            filter_expression=f'video_id = "{video_id}"',
            offset=0,
            limit=1000,
        )
        existing_ids = [hit["id"] for hit in existing.get("hits", [])]
        if existing_ids:
            task = self._request(
                "POST",
                f"/indexes/{self.settings.search_index_uid}/documents/delete-batch",
                json=existing_ids,
                tolerate_statuses={202},
            )
            self._wait_for_task(task.get("taskUid"))

        if documents:
            task = self._request(
                "POST",
                f"/indexes/{self.settings.search_index_uid}/documents",
                json=documents,
                tolerate_statuses={202},
            )
            self._wait_for_task(task.get("taskUid"))

    def delete_video_documents(self, *, video_id: str) -> None:
        if not self.enabled:
            return
        self.replace_video_documents(video_id=video_id, documents=[])

    def _wait_for_task(self, task_uid: int | None) -> None:
        if task_uid is None:
            return

        deadline = time.monotonic() + self.settings.search_task_wait_seconds
        while time.monotonic() < deadline:
            payload = self._request("GET", f"/tasks/{task_uid}")
            status_value = payload.get("status")
            if status_value == "succeeded":
                return
            if status_value == "failed":
                raise SearchBackendUnavailable("Search indexing task failed.")
            time.sleep(0.05)

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        tolerate_statuses: set[int] | None = None,
    ) -> dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if self.settings.search_api_key:
            headers["Authorization"] = f"Bearer {self.settings.search_api_key}"

        try:
            response = httpx.request(
                method,
                f"{self.settings.search_url.rstrip('/')}{path}",
                headers=headers,
                json=json,
                timeout=self.settings.search_timeout_seconds,
            )
        except httpx.HTTPError as exc:
            raise SearchBackendUnavailable("Search backend request failed.") from exc

        if tolerate_statuses and response.status_code in tolerate_statuses:
            return response.json() if response.content else {}

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise SearchBackendUnavailable("Search backend request failed.") from exc

        return response.json() if response.content else {}


def get_search_backend() -> MeiliSearchBackend:
    return MeiliSearchBackend()