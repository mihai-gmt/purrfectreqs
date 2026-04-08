 file: features/auth/20260407_basic_search_user_api.feature
# Version: 1.0
# Last Updated: 2026-04-07
# Type: API
# This feature contains the first iteration of the API endpoint for searching users.

Feature: Search users
  As a user of the application
  I want to be able to search for other users by email or username
  So that I can find them on the platform

    @auth @search_users @smoke @critical @happy_path
    Scenario: Successfully find user by email address
    Given the search user API (GET auth/search-user) is available
    And the user I want to search exists as a registered user
        | email | username | first_name | last_name |
        | john.doe@example.com | john.doe | john | doe |
    When I search the user by email address
        | email |
        | john.doe@example.com |
    Then the search returns 200 status
    And response wrapped in {"data": {...}, "code": ..., "message": "...", "correlation_id": "..."}
    And the response.data contains the user information
        | email | username | first_name | last_name |
        | john.doe@example.com | john.doe | john | doe |
    And code is the response HTTP code
    And message is "User found."
    And correlation_id is a valid UUID

    @auth @search_users @smoke @critical @happy_path
    Scenario: Successfully find user by username
    Given the search user API (GET auth/search-user) is available
    And the user I want to search exists as a registered user
        | email | username | first_name | last_name |
        | john.doe@example.com | john.doe | john | doe |
    When I search the user by username
        | username |
        | john.doe |
    Then the search returns 200 status
    And response wrapped in {"data": {...}, "code": ..., "message": "...", "correlation_id": "..."}
    And the response.data contains the user information
        | email | username | first_name | last_name |
        | john.doe@example.com | john.doe | john | doe |
    And code is the response HTTP code
    And message is "User found."
    And correlation_id is a valid UUID

    @auth @search_users @smoke @critical @happy_path
    Scenario: Successfully find user by both email and username
    Given the search user API (GET auth/search-user) is available
    And the user I want to search exists as a registered user
        | email | username | first_name | last_name |
        | john.doe@example.com | john.doe | john | doe |
    And I search the user by both email and username
    And the email and username I search belong to the same user
    When I search the user by email and username
        | email | username |
        | john.doe@example.com | john.doe |
    Then the search returns 200 status
    And response wrapped in {"data": {...}, "code": ..., "message": "...", "correlation_id": "..."}
    And the response.data contains the user information
        | email | username | first_name | last_name |
        | john.doe@example.com | john.doe | john | doe |
    And code is the response HTTP code
    And message is "User found."
    And correlation_id is a valid UUID

    @auth @search_users @smoke @critical @fail
    Scenario: Search for non-existent user only by email address
    Given the search user API (GET auth/search-user) is available
    And the user I want to search by email address does not exists
    When I search the user by email address
        | email |
        | john.doe@example.com |
    Then the search returns 404 status
    And response wrapped in {"data": {...}, "code": ..., "message": "...", "correlation_id": "..."}
    And response.data is empty
    And code is the response HTTP code
    And message is "User not found"
    And correlation_id is a valid UUID

    @auth @search_users @smoke @critical @fail
    Scenario: Search for non-existent user only by email address
    Given the search user API (GET auth/search-user) is available
    And the user I want to search by email address does not exists
    When I search the user by email address
        | email |
        | john.doe@example.com |
    Then the search returns 404 status
    And response wrapped in {"data": {...}, "code": ..., "message": "...", "correlation_id": "..."}
    And response.data is empty
    And code is the response HTTP code
    And message is "User not found"
    And correlation_id is a valid UUID