Feature: Shopping Cart

  @skip
  Scenario: Add item to cart
    Given the user has a product in view
    When the user clicks "Add to cart"
    Then the cart should contain 1 item
