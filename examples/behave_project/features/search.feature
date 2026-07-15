Feature: Search

  Scenario: Search for a product that does not exist
    Given the user is on the search page
    When the user searches for "nonexistent-product"
    Then the search results should show "No results found"
