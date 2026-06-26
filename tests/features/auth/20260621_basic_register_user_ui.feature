# file: features/auth/20260621_basic_register_user_ui.feature
# Version: 1.0
# Last Updated: 2026-06-21
# Type: UI
# This feature covers the browser (server-rendered HTML) flow for registering a
# new user through the registration page. It is the UI counterpart to
# 20260407_basic_register_user_api.feature (the JSON API flow).
#
# Scope for this iteration: the happy path (successful registration), the
# "email already registered" failure, and the honeypot bot-rejection path
# (docs/SECURITY.md §11, which outranks this feature and mandates server-side
# handling on all public forms). All other validation failures (password policy,
# email format, missing fields, duplicate username) are already covered by the API
# feature and are out of scope here.
#
# Browser flow (docs/SECURITY.md §4 and §14): with Accept: text/html the server
# responds with an HTTP 303 redirect on success. Registration issues NO tokens and
# NO cookies — the visitor logs in separately afterwards. New accounts are created
# with role "super_user" and status "active" (docs/SECURITY.md §4, §5).

Feature: Register a new account from the browser
  As a new visitor using a web browser
  I want to register for an account through the registration page
  So that I can then log in and use the application

  Background:
    Given I am an unauthenticated visitor
    And I am on the registration page at "/auth/register"
    And the page is server-rendered HTML containing a registration form
    And the form includes a hidden honeypot field

  @auth @new_user_registration @ui @smoke @critical @happy_path
  Scenario: Successful registration redirects the visitor to the login page
    Given no account exists for the email "john.doe@example.com" or the username "john.doe"
    When I fill in the registration form with:
        | email | password | username | first_name | last_name |
        | john.doe@example.com | Valid1234! | john.doe | John | Doe |
    And I leave the hidden honeypot field empty
    And I submit the registration form
    Then my account is created with status "active" and role "super_user"
    And no authentication tokens or cookies are issued by registration
    And I receive an HTTP 303 redirect with the Location header set to "/auth/login"
    And my browser lands on the login page

  @auth @new_user_registration @ui @smoke @critical @fail
  Scenario: Registration is rejected when the email is already registered
    Given an account already exists with the email "john.doe@example.com"
    When I fill in the registration form with:
        | email | password | username | first_name | last_name |
        | john.doe@example.com | Valid1234! | john.doe1 | John | Doe |
    And I leave the hidden honeypot field empty
    And I submit the registration form
    Then no new account is created
    And I receive an HTTP 409 response
    And I remain on the registration page
    And the form displays the error message "Email address already in use. Please login with your existing account!"

  @auth @new_user_registration @ui @smoke @critical @fail @honeypot
  Scenario: Registration is silently rejected when the honeypot field is filled
    Given no account exists for the email "bot.victim@example.com" or the username "bot.victim"
    When I fill in the registration form with:
        | email | password | username | first_name | last_name |
        | bot.victim@example.com | Valid1234! | bot.victim | Bot | Victim |
    And the hidden honeypot field is filled with "http://spam.example.com"
    And I submit the registration form
    Then no account is created
    And I receive an HTTP 303 redirect with the Location header set to "/auth/login"
    And the response is indistinguishable from a successful registration
    And the bot detection event is logged at WARNING level with the correlation ID
