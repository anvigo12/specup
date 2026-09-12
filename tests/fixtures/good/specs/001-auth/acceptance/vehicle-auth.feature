# Tag binding, per the ID grammar. The @SCEN- tag is the scenario's identity in the graph:
# gherkin-tag-scan reads it to emit SCEN-* --executes--> AC-*, so a scenario without one is
# unaddressable and derives nothing. @REQ- sits on the Feature because Gherkin tags are
# inherited; the @AC- tags sit on their own scenarios because they are not shared.
@REQ-AUTH-0014
Feature: Vehicle certificate authentication

  @SCEN-AUTH-0031
  @AC-AUTH-0014-0003
  @TC-AUTH-0031
  Scenario: Invalid vehicle certificate
    Given a vehicle has an invalid certificate
    When the vehicle requests authentication
    Then the authentication request is rejected

  @SCEN-AUTH-0032
  @NON-FR-AUTH-0017
  @AC-AUTH-0014-0004
  @TC-AUTH-0031
  Scenario: Authentication stays within the latency budget
    Given a fleet of vehicles with valid certificates
    When they request authentication under nominal load
    Then the p95 authentication latency is within 200ms
