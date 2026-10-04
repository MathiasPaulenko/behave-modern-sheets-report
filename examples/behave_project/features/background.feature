Feature: Shopping with an authenticated user
  Scenarios that share a logged-in state via a common background.

  Background:
    Given the user is on the login page
    When the user enters "alice" as username
    When the user clicks "login"

  Scenario: Viewing the cart as a logged-in user
    Given the user has items in the cart
    Then the cart should contain 1 item

  Scenario: Searching as a logged-in user
    When the user searches for "laptop"
    Then the user should be logged in
