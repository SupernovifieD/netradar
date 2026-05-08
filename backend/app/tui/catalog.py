"""Backward-compatible re-export of shared service catalog helpers."""

from app.services_catalog import ServiceCatalog, ServiceCatalogItem

__all__ = ["ServiceCatalog", "ServiceCatalogItem"]
