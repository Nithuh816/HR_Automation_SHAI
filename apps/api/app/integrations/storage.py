from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

import boto3
from botocore.client import Config

from app.config import settings


class ObjectStorage(ABC):
    @abstractmethod
    def put(
        self, key: str, body: bytes, content_type: str = "application/octet-stream"
    ) -> None: ...

    @abstractmethod
    def get(self, key: str) -> bytes: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...

    @abstractmethod
    def presigned_get(self, key: str, ttl_seconds: int | None = None) -> str: ...


class LocalFsStorage(ObjectStorage):
    """For unit tests and minimal local dev without MinIO running."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        p = self.root / key
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def put(self, key: str, body: bytes, content_type: str = "application/octet-stream") -> None:
        self._path(key).write_bytes(body)

    def get(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)

    def presigned_get(self, key: str, ttl_seconds: int | None = None) -> str:
        return f"file://{self._path(key).resolve()}"


class S3CompatibleStorage(ObjectStorage):
    """Works against MinIO, Cloudflare R2, and AWS S3."""

    def __init__(self) -> None:
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url or None,
            region_name=settings.s3_region,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            config=Config(signature_version="s3v4"),
        )
        self._bucket = settings.storage_bucket

    def put(self, key: str, body: bytes, content_type: str = "application/octet-stream") -> None:
        self._client.put_object(Bucket=self._bucket, Key=key, Body=body, ContentType=content_type)

    def get(self, key: str) -> bytes:
        obj = self._client.get_object(Bucket=self._bucket, Key=key)
        return bytes(obj["Body"].read())

    def delete(self, key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=key)

    def presigned_get(self, key: str, ttl_seconds: int | None = None) -> str:
        return str(
            self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": key},
                ExpiresIn=ttl_seconds or settings.s3_presign_ttl_seconds,
            )
        )


def get_storage() -> ObjectStorage:
    if settings.storage_backend == "local":
        return LocalFsStorage(Path(".local-storage"))
    return S3CompatibleStorage()
