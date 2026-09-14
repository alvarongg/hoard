"""REST endpoints for item transactions and investment."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from api.dependencies import get_transaction_service
from api.schemas.transaction import (
    ItemInvestment,
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
)
from api.services.transaction_service import TransactionService

router = APIRouter(tags=["transactions"])


@router.get(
    "/collection-items/{collection_item_id}/transactions",
    response_model=list[TransactionResponse],
)
async def list_transactions(
    collection_item_id: str,
    service: TransactionService = Depends(get_transaction_service),
) -> list[TransactionResponse]:
    """List transactions for a collection item, newest first."""
    return await service.list(collection_item_id)


@router.post(
    "/collection-items/{collection_item_id}/transactions",
    response_model=TransactionResponse,
    status_code=201,
)
async def create_transaction(
    collection_item_id: str,
    data: TransactionCreate,
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionResponse:
    """Create a transaction for a collection item."""
    return await service.create(collection_item_id, data)


@router.put(
    "/transactions/{transaction_id}",
    response_model=TransactionResponse,
)
async def update_transaction(
    transaction_id: str,
    data: TransactionUpdate,
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionResponse:
    """Update a transaction."""
    return await service.update(transaction_id, data)


@router.delete(
    "/transactions/{transaction_id}",
    response_model=ItemInvestment,
)
async def delete_transaction(
    transaction_id: str,
    service: TransactionService = Depends(get_transaction_service),
) -> ItemInvestment:
    """Delete a transaction and return the recomputed investment summary."""
    return await service.delete(transaction_id)


@router.get(
    "/collection-items/{collection_item_id}/investment",
    response_model=ItemInvestment,
)
async def get_investment(
    collection_item_id: str,
    service: TransactionService = Depends(get_transaction_service),
) -> ItemInvestment:
    """Return the investment summary for a collection item."""
    return await service.get_investment(collection_item_id)
