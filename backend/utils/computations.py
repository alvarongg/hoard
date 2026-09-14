"""Pure computation functions for business calculations.

These functions encapsulate the arithmetic rules of the domain without
any database dependency. They serve as the single source of truth for
calculations that may be computed differently depending on the database
dialect (PostgreSQL GENERATED columns vs SQLite in-memory computation).

All functions treat nulls explicitly and return appropriate types.
"""

from __future__ import annotations

from decimal import Decimal


def transaction_total(
    amount: Decimal | None,
    shipping_cost: Decimal | None,
    tax_amount: Decimal | None,
    other_fees: Decimal | None,
) -> Decimal:
    """Calculate the total amount of a transaction.

    Sums all cost components, treating null values as zero. This function
    replicates the computation of the GENERATED column
    `item_transactions.total_amount` in PostgreSQL.

    Args:
        amount: The base transaction amount (purchase price, sale price, etc.).
        shipping_cost: The cost of shipping, if any.
        tax_amount: The tax amount, if any.
        other_fees: Any additional fees, if any.

    Returns:
        The total transaction amount, never null. Returns Decimal('0') if
        all inputs are null.

    Example:
        >>> transaction_total(Decimal('100.00'), Decimal('10.00'), None, Decimal('5.00'))
        Decimal('115.00')
        >>> transaction_total(None, None, None, None)
        Decimal('0')
    """
    return (
        (amount or Decimal("0"))
        + (shipping_cost or Decimal("0"))
        + (tax_amount or Decimal("0"))
        + (other_fees or Decimal("0"))
    )


def available_stock(quantity_total: int, quantity_in_use: int) -> int:
    """Calculate the available stock of an accessory.

    Computes the difference between total quantity and quantity in use.
    This function replicates the computation of the GENERATED column
    `accessories_stock.quantity_available` in PostgreSQL.

    Args:
        quantity_total: The total quantity of the accessory in stock.
        quantity_in_use: The quantity currently assigned to collection items.

    Returns:
        The available (unassigned) quantity. May be negative if more items
        are assigned than exist in stock (data inconsistency).

    Example:
        >>> available_stock(100, 25)
        75
        >>> available_stock(10, 0)
        10
    """
    return quantity_total - quantity_in_use


def roi_percentage(
    invested: Decimal,
    current_value: Decimal,
) -> Decimal | None:
    """Calculate the return on investment (ROI) as a percentage.

    The ROI is computed as ((current_value - invested) / invested) * 100.
    Returns None when invested is zero to avoid division by zero.

    Args:
        invested: The total amount invested (purchase price, transaction
            costs, etc.). Can be zero or negative.
        current_value: The current market value of the item.

    Returns:
        The ROI as a percentage, or None if invested is zero.

    Example:
        >>> roi_percentage(Decimal('100.00'), Decimal('150.00'))
        Decimal('50.00')
        >>> roi_percentage(Decimal('100.00'), Decimal('80.00'))
        Decimal('-20.00')
        >>> roi_percentage(Decimal('0'), Decimal('100.00'))
        None
    """
    if invested == 0:
        return None
    return ((current_value - invested) / invested) * Decimal("100")


def is_item_complete(
    required_names: set[str],
    present_names: set[str],
) -> bool:
    """Determine if a collection item is complete.

    An item is considered complete when all required components are present.
    Required components are defined by the `standard_components` table for
    each sub-category with `component_type == "required"`.

    Args:
        required_names: Set of component names that are required for the
            item to be considered complete.
        present_names: Set of component names that are marked as present
            for the item.

    Returns:
        True if all required components are present (or if no components
        are required), False otherwise.

    Example:
        >>> is_item_complete({'box', 'manual'}, {'box', 'manual', 'insert'})
        True
        >>> is_item_complete({'box', 'manual'}, {'box'})
        False
        >>> is_item_complete(set(), {'box', 'manual'})
        True
    """
    if not required_names:
        return True
    return required_names.issubset(present_names)
