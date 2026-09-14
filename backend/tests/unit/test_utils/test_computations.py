"""Tests for utils.computations pure calculation functions.

Validates: Requirements 11.5, 12.9, 7.7, 5.5, 19.10
"""

from decimal import Decimal

import pytest

from utils.computations import (
    available_stock,
    is_item_complete,
    roi_percentage,
    transaction_total,
)


class TestTransactionTotal:
    """Tests for transaction_total calculation.

    Requirement 11.5: total_amount = amount + shipping_cost + tax_amount + other_fees
    Null values are treated as zero.
    """

    def test_all_fields_present_returns_sum(self) -> None:
        result = transaction_total(
            amount=Decimal("100.00"),
            shipping_cost=Decimal("10.00"),
            tax_amount=Decimal("15.50"),
            other_fees=Decimal("5.00"),
        )
        assert result == Decimal("130.50")

    def test_partial_nulls_treats_nulls_as_zero(self) -> None:
        result = transaction_total(
            amount=Decimal("100.00"),
            shipping_cost=None,
            tax_amount=Decimal("10.00"),
            other_fees=None,
        )
        assert result == Decimal("110.00")

    def test_all_nulls_returns_zero(self) -> None:
        result = transaction_total(
            amount=None,
            shipping_cost=None,
            tax_amount=None,
            other_fees=None,
        )
        assert result == Decimal("0")

    def test_only_amount_returns_amount(self) -> None:
        result = transaction_total(
            amount=Decimal("50.00"),
            shipping_cost=None,
            tax_amount=None,
            other_fees=None,
        )
        assert result == Decimal("50.00")

    def test_zero_values_sum_correctly(self) -> None:
        result = transaction_total(
            amount=Decimal("0"),
            shipping_cost=Decimal("0"),
            tax_amount=Decimal("0"),
            other_fees=Decimal("0"),
        )
        assert result == Decimal("0")

    def test_negative_amounts_supported(self) -> None:
        """Negative amounts may represent refunds or adjustments."""
        result = transaction_total(
            amount=Decimal("-10.00"),
            shipping_cost=Decimal("5.00"),
            tax_amount=None,
            other_fees=None,
        )
        assert result == Decimal("-5.00")


class TestAvailableStock:
    """Tests for available_stock calculation.

    Requirement 12.9: quantity_available = quantity_total - quantity_in_use
    """

    def test_standard_case_returns_difference(self) -> None:
        result = available_stock(quantity_total=100, quantity_in_use=25)
        assert result == 75

    def test_zero_in_use_returns_total(self) -> None:
        result = available_stock(quantity_total=50, quantity_in_use=0)
        assert result == 50

    def test_fully_used_returns_zero(self) -> None:
        result = available_stock(quantity_total=100, quantity_in_use=100)
        assert result == 0

    def test_zero_total_and_zero_in_use_returns_zero(self) -> None:
        result = available_stock(quantity_total=0, quantity_in_use=0)
        assert result == 0

    def test_over_assignment_returns_negative(self) -> None:
        """Data inconsistency: more assigned than exists."""
        result = available_stock(quantity_total=10, quantity_in_use=15)
        assert result == -5


class TestRoiPercentage:
    """Tests for roi_percentage calculation.

    Requirement 7.7: When invested is zero, return None to avoid division by zero.
    """

    def test_positive_roi_returns_percentage(self) -> None:
        result = roi_percentage(
            invested=Decimal("100.00"),
            current_value=Decimal("150.00"),
        )
        assert result == Decimal("50.00")

    def test_negative_roi_returns_negative_percentage(self) -> None:
        result = roi_percentage(
            invested=Decimal("100.00"),
            current_value=Decimal("80.00"),
        )
        assert result == Decimal("-20.00")

    def test_zero_invested_returns_none(self) -> None:
        """Avoid division by zero when no investment was made."""
        result = roi_percentage(
            invested=Decimal("0"),
            current_value=Decimal("100.00"),
        )
        assert result is None

    def test_zero_invested_zero_value_returns_none(self) -> None:
        result = roi_percentage(
            invested=Decimal("0"),
            current_value=Decimal("0"),
        )
        assert result is None

    def test_same_value_returns_zero_roi(self) -> None:
        result = roi_percentage(
            invested=Decimal("100.00"),
            current_value=Decimal("100.00"),
        )
        assert result == Decimal("0")

    def test_double_value_returns_100_percent(self) -> None:
        result = roi_percentage(
            invested=Decimal("50.00"),
            current_value=Decimal("100.00"),
        )
        assert result == Decimal("100.00")

    def test_negative_invested_with_positive_value(self) -> None:
        """Edge case: negative investment (e.g., profit already taken)."""
        result = roi_percentage(
            invested=Decimal("-100.00"),
            current_value=Decimal("50.00"),
        )
        # (-100.00 - (-100.00)) / -100.00 * 100 = 0 / -100.00 * 100 = 0
        # Actually: (50 - (-100)) / -100 * 100 = 150 / -100 * 100 = -150
        assert result == Decimal("-150.00")


class TestIsItemComplete:
    """Tests for is_item_complete determination.

    Requirement 5.5: Item is complete when all required components are present.
    """

    def test_all_required_present_returns_true(self) -> None:
        result = is_item_complete(
            required_names={"box", "manual"},
            present_names={"box", "manual", "insert"},
        )
        assert result is True

    def test_only_required_present_returns_true(self) -> None:
        result = is_item_complete(
            required_names={"box", "manual"},
            present_names={"box", "manual"},
        )
        assert result is True

    def test_missing_required_returns_false(self) -> None:
        result = is_item_complete(
            required_names={"box", "manual"},
            present_names={"box"},
        )
        assert result is False

    def test_empty_required_returns_true(self) -> None:
        """No requirements means item is trivially complete."""
        result = is_item_complete(
            required_names=set(),
            present_names={"box", "manual"},
        )
        assert result is True

    def test_empty_required_and_empty_present_returns_true(self) -> None:
        result = is_item_complete(
            required_names=set(),
            present_names=set(),
        )
        assert result is True

    def test_missing_all_required_returns_false(self) -> None:
        result = is_item_complete(
            required_names={"box", "manual", "insert"},
            present_names=set(),
        )
        assert result is False

    def test_extra_present_components_ignored(self) -> None:
        """Extra components don't affect completeness check."""
        result = is_item_complete(
            required_names={"box"},
            present_names={"box", "manual", "insert", "poster"},
        )
        assert result is True

    def test_case_sensitive_component_names(self) -> None:
        """Component names are case-sensitive."""
        result = is_item_complete(
            required_names={"Box", "Manual"},
            present_names={"box", "manual"},
        )
        assert result is False
