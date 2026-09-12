@REQ-AUTH-0014
@AC-AUTH-0014-0003
Feature: Vehicle certificate authentication

  @TC-AUTH-0031
  Scenario: Invalid vehicle certificate
    Given a vehicle has an invalid certificate
    When the vehicle requests authentication
    Then the authentication request is rejected
