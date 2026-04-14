 file: features/auth/20260407_basic_login_user_api.feature
# Version: 1.0
# Last Updated: 2026-04-08
# Type: API
# This feature contains the first iteration of the API endpoint for user login.

Feature: Login users
  As a registered user of the application
  I want to be able to login with my credentials
  So that I can access the application functionalities

    @auth @login_users @smoke @critical @happy_path
    Scenario: Successful login
    Given the login API endpoint (POST auth/login) is available
    And the user exists as a registered user with the details
        | email | password |
        |john.doe@example.com | GoodPassword1* |
    And the user account status is "active"
    When I login with my email address and password
        | email | password |
        |john.doe@example.com | GoodPassword1 |
    Then the response status is 200
    And response is wrapped in {"data": {...}, "message": "...", "correlation_id": "..."}
    And response.data contanins a valid authorization token
    And message is "Login successful."
    And correlation_id is valid UUID
    And failed_login_attempts is set to 0

    @auth @login_users @smoke @critical @negative_path
    Scenario: User is not logged in when using incorrect email and password combination
    Given the login API endpoint (POST auth/login) is available
    And the user exists as a registered user with the details
        | email | password |
        |john.doe@example.com | GoodPassword1* |
    And the user account status is "active"
    And the user DB field failed_login_attempts is < 4
    When I try to login with incorrect username and password combination
        | email | password |
        | john.doe@example | WrongPass1* |
    Then the response status is 401
    And the response is wrapped in {"error_code": ..., "message": …, "correlation_id": …, "details": {}}
    And the error_code is "UNAUTHORIZED"
    And message is "Login failed. You must have used an incorrect email address or password."
    And correlation_id is a valid UUID
    And response.details is empty
    And the user DB field failed_login_attempts is incremented by 1

    @auth @login_users @smoke @critical @negative_path @lock_user_account
    Scenario: Lock user account when failed_login_attempts counter reaches 5 failed logins
    Given the login API endpoint (POST auth/login) is available
    And the user exists as a registered user with the details
        | email | password |
        | john.doe@example.com | GoodPassword1* |
    And the user account status is "active"
    And the user DB field failed_login_attempts is equal to 4
    When the user logs in with incorrect email and password combination
        | email | password |
        | john.doe@example | WrongPass1* |
    Then the response status is 401
    And the response is wrapped in {"error_code": ..., "message": …, "correlation_id": …, "details": {}}
    And the error_code is "UNAUTHORIZED"
    And message is "Login failed. Your account has been temporarily locked for 30 minutes due to multiple failed login attempts. Either wait 30 minutes before trying again or reset your password now."
    And correlation_id is a valid UUID
    And response.details is empty
    And the user DB field failed_login_attempts is incremented by 1
    And the user DB field failed_login_attempts reaches 5
    And the user account status is updated to "locked
    And the user DB field locked_until is updated with UTC aware timestamp of request plus 30 minutes

    @auth @login_users @smoke @critical @happy_path @reset_failed_login_attempts @unlock_locked_account
    Scenario: Reset failed_login_attempts counter and set user account status to active on successful login
    Given the login API endpoint (POST auth/login) is available
    And the user exists as a registered user with the details
        | email | password |
        | john.doe@example.com | GoodPassword1* |
    And the user account status is "locked"
    And the user db field locked_until is less than current timestamp
    And the user successfuly logs in with the correct details
        | email | password |
        | john.doe@example.com | GoodPassword1* |
    When the user is successfully logged in
    Then the response status is 200
    And response is wrapped in {"data": {...}, "message": "...", "correlation_id": "..."}
    And response.data contanins a valid authorization token
    And message is "Login successful."
    And correlation_id is valid UUID
    And failed_login_attempts is set to 0
    And the account status is set to "active"
    And the user DB field failed_login_attempts is set to 0

    @auth @login_users @smoke @critical @negative_path @account_locked
    Scenario: Login with correct credentials fails when account is locked and lock duration did not expire
    Given the login API endpoint (POST auth/login) is available
    And the user exists as a registered user with the details
        | email | password |
        | john.doe@example.com | GoodPassword1* |
    And the user account status is "locked"
    And the user db field locked_until is not less than current timestamp
    When the user logs in with the correct details
        | email | password |
        | john.doe@example.com | GoodPassword1* |
    The the response status is 423
    And the response is wrapped in {"error_code": ..., "message": …, "correlation_id": …, "details": {}}
    And the error_code is "ACCOUNT_LOCKED"
    And the message is "Account is locked due to more than 5 failed login attempts. Either wait for the lock to expire or reset your password now."