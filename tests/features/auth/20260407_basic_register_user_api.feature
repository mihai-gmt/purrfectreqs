# file: features/auth/20260407_basic_register_user_api.feature
# Version: 1.0
# Last Updated: 2026-04-05
# Type: API
# This feature contains the first iteration of the API endpoint for registering new 
# users and its behaviour. No user interface components present in these requirements.

Feature: New user Account Registration
  As a new visitor
  I want to create a new account
  So that I can access personalized features and use the service

    @auth @new_user_registration @smoke @critical @happy_path
    Scenario: Successful registration with valid credentials that do not exist in the DB
        Given no user account exist for the following user registration data:
            | email | password | username |
            | john.doe@example.com | Valid1234! | john.doe |
        When I register with the following details:
            | email | password | username | first_name | last_name |
            | john.doe@example.com | Valid1234! | john.doe | John | Doe |
        Then my account is created with status "active" and role "super_user"
        And I receive a 201 response
        And I receive a confirmation message that my account was created
        And the message is "Congrats! Your account has been successfully created."

    @auth @new_user_registration @smoke @critical @fail
    Scenario: Registration failure when email already exists
        Given an account already exists with the email address "john.doe@example.com"
        When I register with the following details:
            | email | password | username | first_name | last_name |
            | john.doe@example.com | Valid1234! | john.doe1 | John | Doe |
        Then my account is not created
        And I receive a 409 response
        And the response message is "Email address already in use. Please login with your existing account!"

    @auth @new_user_registration @smoke @critical @fail
    Scenario: Registration failure when username already exists
        Given an account already exists with email address "john.doe@example.com" and username "john.doe"
        When I register with the following details:
            | email | password | username | first_name | last_name |
            | john.doe2@example.com | Valid1234! | john.doe | John | Doe |
        Then my account is not created
        And I receive a 409 response
        And the response message is "Username already in use. Please choose a different username!"

    @auth @new_user_registration @smoke @critical @fail
    Scenario: Registration failure when password is too short
        
        When I register with the following details:
            | email | password | username | first_name | last_name |
            | john.doe4@example.com | weak | john.doe4 | John | Doe |
        Then my account is not created
        And I receive a 422 response
        And the response message is "Password does not meet the complexity requirements. Please fix it."
    
    @auth @new_user_registration @smoke @critical @fail
    Scenario: Registration failure when missing required fields from registration payload

        When I register with the following details:
            | email | password | username | first_name | last_name |
            | john.doe5@example.com |  |  | John | Doe |
        Then my account is not created
        And I receive a 422 response
        And the response message is "Missing required registration details. Please fix it!"

    @auth @new_user_registration @smoke @critical @fail
    Scenario: Registration failure when password has no letters and special characters
        
        When I register with the following details:
            | email | password | username | first_name | last_name |
            | john.doe6@example.com | 11111111111111 | john.doe4 | John | Doe |
        Then my account is not created
        And I receive a 422 response
        And the response message is "Password does not meet the complexity requirements. Please fix it."

    @auth @new_user_registration @smoke @critical @fail
    Scenario: Registration failure when password has no special characters
        
        When I register with the following details:
            | email | password | username | first_name | last_name |
            | john.doe7@example.com | Weak1234 | john.doe4 | John | Doe |
        Then my account is not created
        And I receive a 422 response
        And the response message is "Password does not meet the complexity requirements. Please fix it."

    @auth @new_user_registration @smoke @critical @fail
    Scenario: Registration failure when password has no letters
        
        When I register with the following details:
            | email | password | username | first_name | last_name |
            | john.doe8@example.com | 1234!!!!!! | john.doe4 | John | Doe |
        Then my account is not created
        And I receive a 422 response
        And the response message is "Password does not meet the complexity requirements. Please fix it."

    @auth @new_user_registration @smoke @critical @fail
    Scenario: Registration failure when password has no numbers and special characters
        
        When I register with the following details:
            | email | password | username | first_name | last_name |
            | john.doe9@example.com | WeakWeakWeakWeakWeak | john.doe4 | John | Doe |
        Then my account is not created
        And I receive a 422 response
        And the response message is "Password does not meet the complexity requirements. Please fix it."
    
    @auth @new_user_registration @smoke @critical @fail
    Scenario: Registration failure when email is missing the domain
        When I register with the following details:
            | email | password | username | first_name | last_name |
            | john.doe9@ | GoodPass123!! | john.doe4 | John | Doe |
        Then my account is not created
        And I receive a 422 response
        And the response message is "Incorrect email address format. Please fix it."

    @auth @new_user_registration @smoke @critical @fail
    Scenario: Registration failure when email is missing the domain suffix
        When I register with the following details:
            | email | password | username | first_name | last_name |
            | john.doe9@example | GoodPass123!! | john.doe4 | John | Doe |
        Then my account is not created
        And I receive a 422 response
        And the response message is "Incorrect email address format. Please fix it."