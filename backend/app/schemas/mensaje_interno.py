"""schemas/mensaje_interno.py — Pydantic schemas for internal messaging (C-20).

MensajeInternoCreate: request body for POST /api/inbox/
MensajeInternoResponder: request body for POST /api/inbox/{id}/responder
MensajeInternoOut: response schema
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

_FORBID = ConfigDict(extra="forbid")
_FORBID_FROM_ATTRS = ConfigDict(extra="forbid", from_attributes=True)


class MensajeInternoCreate(BaseModel):
    """Request body for POST /api/inbox/ — send a new message."""

    model_config = _FORBID

    destinatario_id: uuid.UUID = Field(..., description="Recipient user UUID (must be in same tenant)")
    asunto: str = Field(..., min_length=1, max_length=255, description="Message subject")
    cuerpo: str = Field(..., min_length=1, description="Message body")


class MensajeInternoResponder(BaseModel):
    """Request body for POST /api/inbox/{id}/responder — reply in a thread."""

    model_config = _FORBID

    cuerpo: str = Field(..., min_length=1, description="Reply body")


class MensajeInternoOut(BaseModel):
    """Response schema for a single MensajeInterno."""

    model_config = _FORBID_FROM_ATTRS

    id: uuid.UUID
    tenant_id: uuid.UUID
    remitente_id: uuid.UUID
    destinatario_id: uuid.UUID
    asunto: str
    cuerpo: str
    leido: bool
    hilo_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
