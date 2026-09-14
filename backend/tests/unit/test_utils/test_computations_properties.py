"""Property-based tests for utils.computations pure calculation functions.

These tests use Hypothesis to verify universal properties of the computation
functions across a wide range of inputs.
"""

from decimal import Decimal

from hypothesis import given, settings
from hypothesis import strategies as st

from utils.computations import roi_percentage, transaction_total


# Strategy for non-negative decimals (0.00 to 999999.99, with 2 decimal places)
non_negative_decimal = st.decimals(
    min_value=Decimal("0"),
    max_value=Decimal("999999.99"),
    places=2,
)

# Strategy for optional non-negative decimals (Decimal or None)
optional_non_negative_decimal = st.one_of(
    st.none(),
    non_negative_decimal,
)

# Strategy for Decimal values with reasonable precision (including negative values)
decimal_strategy = st.decimals(
    min_value=Decimal("-1000000"),
    max_value=Decimal("1000000"),
    allow_nan=False,
    allow_infinity=False,
    places=2,
)


class TestTransactionTotalProperties:
    """Property-based tests for transaction_total calculation.

    Validates: Requirements 11.4, 11.5
    """

    @given(
        amount=optional_non_negative_decimal,
        shipping_cost=optional_non_negative_decimal,
        tax_amount=optional_non_negative_decimal,
        other_fees=optional_non_negative_decimal,
    )
    @settings(max_examples=100)
    def test_total_is_sum_with_nulls_as_zero(
        self,
        amount: Decimal | None,
        shipping_cost: Decimal | None,
        tax_amount: Decimal | None,
        other_fees: Decimal | None,
    ) -> None:
        """Property 1: total_amount is the sum of all inputs, treating nulls as zero.

        Validates: Requirements 11.4, 11.5
        """
        result = transaction_total(
            amount=amount,
            shipping_cost=shipping_cost,
            tax_amount=tax_amount,
            other_fees=other_fees,
        )

        # Calculate expected sum treating None as Decimal("0")
        expected = (
            (amount or Decimal("0"))
            + (shipping_cost or Decimal("0"))
            + (tax_amount or Decimal("0"))
            + (other_fees or Decimal("0"))
        )

        assert result == expected

    @given(
        amount=non_negative_decimal,
        shipping_cost=non_negative_decimal,
        tax_amount=non_negative_decimal,
        other_fees=non_negative_decimal,
    )
    @settings(max_examples=100)
    def test_total_is_non_negative_with_non_negative_inputs(
        self,
        amount: Decimal,
        shipping_cost: Decimal,
        tax_amount: Decimal,
        other_fees: Decimal,
    ) -> None:
        """Property: total_amount is non-negative when all inputs are non-negative.

        Validates: Requirement 11.4
        """
        result = transaction_total(
            amount=amount,
            shipping_cost=shipping_cost,
            tax_amount=tax_amount,
            other_fees=other_fees,
        )

        assert result >= Decimal("0")

    @given(
        amount=optional_non_negative_decimal,
        shipping_cost=optional_non_negative_decimal,
        tax_amount=optional_non_negative_decimal,
        other_fees=optional_non_negative_decimal,
    )
    @settings(max_examples=100)
    def test_total_is_zero_when_all_inputs_are_none(
        self,
        amount: Decimal | None,
        shipping_cost: Decimal | None,
        tax_amount: Decimal | None,
        other_fees: Decimal | None,
    ) -> None:
        """Property: total_amount is Decimal('0') when all inputs are None.

        Validates: Requirement 11.5
        """
        # Filter to only run when all inputs are None
        assume_all_none = (
            amount is None
            and shipping_cost is None
            and tax_amount is None
            and other_fees is None
        )
        if not assume_all_none:
            return

        result = transaction_total(
            amount=amount,
            shipping_cost=shipping_cost,
            tax_amount=tax_amount,
            other_fees=other_fees,
        )

        assert result == Decimal("0")

    @given(
        amount=optional_non_negative_decimal,
        shipping_cost=optional_non_negative_decimal,
        tax_amount=optional_non_negative_decimal,
        other_fees=optional_non_negative_decimal,
    )
    @settings(max_examples=100)
    def test_total_is_commutative(
        self,
        amount: Decimal | None,
        shipping_cost: Decimal | None,
        tax_amount: Decimal | None,
        other_fees: Decimal | None,
    ) -> None:
        """Property: total_amount is commutative (order of inputs doesn't matter).

        Validates: Requirement 11.5
        """
        result1 = transaction_total(
            amount=amount,
            shipping_cost=shipping_cost,
            tax_amount=tax_amount,
            other_fees=other_fees,
        )

        # Same values in different conceptual grouping
        partial_sum = (amount or Decimal("0")) + (shipping_cost or Decimal("0"))
        remaining_sum = (tax_amount or Decimal("0")) + (other_fees or Decimal("0"))
        result2 = partial_sum + remaining_sum

        assert result1 == result2


class TestRoiPercentageProperties:
    """Property-based tests for roi_percentage calculation.

    Validates: Requirements 7.3, 7.6, 7.7
    """

    @given(
        invested=decimal_strategy,
        current_value=decimal_strategy,
    )
    @settings(max_examples=100)
    def test_roi_is_null_iff_invested_is_zero(
        self,
        invested: Decimal,
        current_value: Decimal,
    ) -> None:
        """Property 6: ROI is None if and only if investment is zero.

        Validates: Requirements 7.3, 7.6, 7.7

        This property verifies the exact equivalence:
        - If invested == 0, then roi_percentage returns None
        - If roi_percentage returns None, then invested == 0
        - Otherwise, the formula ((current_value - invested) / invested) * 100 holds
        """
        result = roi_percentage(invested=invested, current_value=current_value)

        if invested == 0:
            # Division by zero case: must return None
            assert result is None, (
                f"Expected None when invested=0, got {result} "
                f"(current_value={current_value})"
            )
        else:
            # Non-zero investment: must return a valid Decimal
            assert result is not None, (
                f"Expected non-None result when invested={invested} != 0 "
                f"(current_value={current_value})"
            )

            # Verify the formula: ((current_value - invested) / invested) * 100
            expected = ((current_value - invested) / invested) * Decimal("100")
            assert result == expected, (
                f"ROI formula mismatch: got {result}, expected {expected} "
                f"(invested={invested}, current_value={current_value})"
            )
