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
    And response wrapped in {"data": {...}, "message": "...", "correlation_id": "..."}
    And the response.data contains the user information
        | email | username | first_name | last_name |
        | john.doe@example.com | john.doe | john | doe |
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
    And response wrapped in {"data": {...}, "message": "...", "correlation_id": "..."}
    And the response.data contains the user information
        | email | username | first_name | last_name |
        | john.doe@example.com | john.doe | john | doe |
    And message is "User found."
    And correlation_id is a valid UUID

    @auth @search_users @smoke @critical @happy_path
    Scenario: Successfully find user by both email and username
    Given the search user API (GET auth/search-user) is available
    And the user I want to search exists as a registered user
        | email | username | first_name | last_name |
        | john.doe@example.com | john.doe | john | doe |
    And I search the user by both email and username
    And the email and username I search belong to the same user ID
    When I search the user by email and username
        | email | username |
        | john.doe@example.com | john.doe |
    Then the search returns 200 status
    And response wrapped in {"data": {...}, "message": "...", "correlation_id": "..."}
    And the response.data contains the user information
        | email | username | first_name | last_name |
        | john.doe@example.com | john.doe | john | doe |
    And message is "User found."
    And correlation_id is a valid UUID

    @auth @search_users @smoke @critical @fail
    Scenario: Search for non-existent user only by email address
    Given the search user API (GET auth/search-user) is available
    And the user I want to search by email address does not exist
    When I search the user by email address
        | email |
        | john.doexyz@example.com |
    Then the search returns 404 status
    And response wrapped in {"data": {...}, "code": ..., "message": "...", "correlation_id": "..."}
    And response.data is empty
    And code is the response HTTP code
    And message is "User not found with email <email>"
    And correlation_id is a valid UUID

    @auth @search_users @smoke @critical @fail
    Scenario: Search for non-existent user only by username
    Given the search user API (GET auth/search-user) is available
    And the user I want to search by username does not exist
    When I search the user by username
        | username |
        | john.doexyz |
    Then the search returns 404 status
    And response wrapped in {"data": {...}, "code": ..., "message": "...", "correlation_id": "..."}
    And response.data is empty
    And code is the response HTTP code
    And message is "User not found for username <username>"
    And correlation_id is a valid UUID

    @auth @search_users @smoke @critical @fail
    Scenario: Search for non-existent user by email address and username
    Given the search user API (GET auth/search-user) is available
    And the user I want to search by both email address and username does not exist
    When I search the user by email address and username
        | email | username |
        | john.doexyz@example.com | john.doexyz |
    Then the search returns 404 status
    And response wrapped in {"data": {...}, "code": ..., "message": "...", "correlation_id": "..."}
    And response.data is empty
    And code is the response HTTP code
    And message is "User not found with email <email> and username <username>"
    And correlation_id is a valid UUID

    @auth @search_users @smoke @critical @fail
    Scenario: User search fails when no user exists for the email and username combination
    Given the search user API (GET auth/search-user) is available
    And a user exists for email address john.doexyz@example.com with the details:
        | email | username | first_name | last_name |
        | john.doexyz@example.com | john.doexyz | john | doe |
    And a different user exists for username john.doeabc with the details:
        | email | username | first_name | last_name |
        | john.doeabc@example.com | john.doeabc | john | doe |
    And no user exists for the combination of email and username
        | email | username |
        | john.doexyz@example.com | john.doeabc |
    When I search the user by email address and username
        | email | username |
        | john.doexyz@example.com | john.doeabc |
    Then the search returns 404 status
    And response wrapped in {"data": {...}, "code": ..., "message": "...", "correlation_id": "..."}
    And response.data is empty
    And code is the response HTTP code
    And message is "User not found with email <email> and username <username>"
    And correlation_id is a valid UUID