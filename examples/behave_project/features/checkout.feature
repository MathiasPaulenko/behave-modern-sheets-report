Feature: Checkout

  Scenario Outline: Checkout with <payment_method>
    Given the user has items in the cart
    When the user selects "<payment_method>" as payment method
    Then the order should be confirmed

    Examples:
      | payment_method |
      | credit_card    |
      | paypal         |
