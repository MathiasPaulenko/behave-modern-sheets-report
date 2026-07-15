"""Minimal step definitions for the example Behave project."""

from behave import given, then, when


@given("the user is on the login page")
def step_on_login_page(context: object) -> None:
    """User navigates to the login page."""


@given("the user is on the search page")
def step_on_search_page(context: object) -> None:
    """User navigates to the search page."""


@given("the user has a product in view")
def step_has_product(context: object) -> None:
    """User is viewing a product."""


@given("the user has items in the cart")
def step_has_items(context: object) -> None:
    """User has items in the shopping cart."""


@when('the user enters "{username}" as username')
def step_enter_username(context: object, username: str) -> None:
    """User enters a username."""
    context.username = username


@when('the user enters "{password}" as password')
def step_enter_password(context: object, password: str) -> None:
    """User enters a password."""
    context.password = password


@when('the user searches for "{query}"')
def step_search(context: object, query: str) -> None:
    """User performs a search."""
    context.search_query = query


@when('the user clicks "{button}"')
def step_click_button(context: object, button: str) -> None:
    """User clicks a button."""


@when('the user selects "{method}" as payment method')
def step_select_payment(context: object, method: str) -> None:
    """User selects a payment method."""
    context.payment_method = method


@then("the user should be logged in")
def step_logged_in(context: object) -> None:
    """Verify the user is logged in."""
    assert True


@then("the user should see an error message")
def step_see_error(context: object) -> None:
    """Verify an error message is shown."""
    assert True


@then('the search results should show "{message}"')
def step_search_results(context: object, message: str) -> None:
    """Verify search results show the expected message."""
    assert False, f"Expected: {message}"


@then("the cart should contain 1 item")
def step_cart_has_item(context: object) -> None:
    """Verify the cart contains one item."""
    assert True


@then("the order should be confirmed")
def step_order_confirmed(context: object) -> None:
    """Verify the order is confirmed."""
    assert True
