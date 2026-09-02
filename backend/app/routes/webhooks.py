from fastapi import APIRouter, Request, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from ..models.db_setup import get_db
from ..schemas.retell import RetellWebhookPayload
from ..services.retell_handler import process_retell_webhook
from pydantic import ValidationError
import os
import hmac
import hashlib
import logging

logger = logging.getLogger("dispatcher.webhooks")

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

RETELL_WEBHOOK_SECRET = os.getenv("RETELL_WEBHOOK_SECRET")

def verify_signature(payload_body: bytes, signature: str) -> bool:
    if not RETELL_WEBHOOK_SECRET:
        # If no secret configured, skip verification (warn in logs in real app)
        return True
        
    expected_signature = hmac.new(
        RETELL_WEBHOOK_SECRET.encode('utf-8'),
        payload_body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)

@router.post("/retell")
async def retell_webhook(
    request: Request,
    x_retell_signature: str = Header(None),
    db: Session = Depends(get_db)
):
    body = await request.body()
    
    if RETELL_WEBHOOK_SECRET and not x_retell_signature:
        raise HTTPException(status_code=401, detail="Missing signature")
        
    if RETELL_WEBHOOK_SECRET and not verify_signature(body, x_retell_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        json_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
    try:
        payload = RetellWebhookPayload(**json_data)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())

    logger.info("Received webhook event=%s, call_id=%s", payload.event, payload.call.call_id)
    result = process_retell_webhook(db, payload)
    return result

