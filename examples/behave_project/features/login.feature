Feature: Login

  Scenario: Successful login with valid credentials
    Given the user is on the login page
    When the user enters "admin" as username
    And the user enters "secret" as password
    Then the user should be logged in

  Scenario: Failed login with wrong password
    Given the user is on the login page
    When the user enters "admin" as username
    And the user enters "wrong" as password
    Then the user should see an error message
