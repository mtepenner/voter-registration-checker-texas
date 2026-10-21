Feature: Texas Voter Registration Status Lookup
  As a Texas resident
  I want to navigate to VoteTexas.gov and populate the official lookup portal from my .env file
  So that I can quickly verify my voter registration status

  Scenario: Populate Texas voter registration lookup form from environment variables
    Given valid voter details are loaded from the environment with COUNTY in all caps
    And the browser is on the VoteTexas registration portal
    When the user follows the "Am I Registered" link to the official lookup portal
    And selects the Name and County lookup criteria if present
    And populates the voter lookup fields using the environment details
    Then the COUNTY value should be formatted in ALL CAPS
    And a final verification screenshot is captured before closing the browser
