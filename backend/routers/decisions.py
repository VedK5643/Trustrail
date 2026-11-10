from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db.engine import get_db
from services.orchestrator import orchestrator

router = APIRouter(prefix="/decisions", tags=["Decisions"])

@router.post("/{txn_id}/approve")
async def approve_held_transaction(
    txn_id: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        res = await orchestrator.approve_transaction(db, txn_id)
        return res
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{txn_id}/deny")
async def deny_held_transaction(
    txn_id: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        res = await orchestrator.deny_transaction(db, txn_id)
        return res
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

