import os
import logging
from pytest_bdd import scenarios, given, when, then, parsers
from playwright.sync_api import Error as PlaywrightError, TimeoutError as PlaywrightTimeoutError
from conftest import capture_screenshot

logger = logging.getLogger(__name__)

scenarios("voter_registration.feature")

START_URL = "https://www.votetexas.gov/register-to-vote/index.html"
FALLBACK_URL = "https://teamrv-mvp.sos.texas.gov/MVP/voterDetails.do"


@given("valid voter details are loaded from the environment with COUNTY in all caps")
def verify_voter_env_loaded(voter_env):
    logger.info(
        "Loaded voter data for %s %s (County: %s, Zip: %s)",
        voter_env["first_name"],
        voter_env["last_name"],
        voter_env["county"],
        voter_env["zip_code"],
    )
    assert voter_env["first_name"], "FIRST_NAME must not be empty"
    assert voter_env["last_name"], "LAST_NAME must not be empty"
    assert voter_env["zip_code"], "ZIP_CODE must not be empty"
    assert voter_env["county"], "COUNTY must not be empty"


@given("the browser is on the VoteTexas registration portal")
def navigate_to_votetexas(browser_session):
    page = browser_session["page"]
    logger.info("Navigating to %s", START_URL)
    page.goto(START_URL, wait_until="domcontentloaded", timeout=30000)


@when(parsers.parse('the user follows the "{link_text}" link to the official lookup portal'))
def open_lookup_portal(browser_session, link_text):
    page = browser_session["page"]
    context = browser_session["context"]

    portal_link = page.locator("a", has_text=link_text).first

    if portal_link.count() > 0:
        href = portal_link.get_attribute("href")
        logger.info("Clicking '%s' portal link (%s)...", link_text, href)
        try:
            with context.expect_page(timeout=10000) as new_page_info:
                portal_link.click()
            new_page = new_page_info.value
            new_page.wait_for_load_state("domcontentloaded", timeout=30000)
            browser_session["page"] = new_page
            logger.info("Switched active tab to lookup portal: %s", new_page.url)
        except PlaywrightTimeoutError:
            logger.debug("Portal opened in current tab; waiting for load state.")
            page.wait_for_load_state("domcontentloaded", timeout=15000)
    else:
        logger.warning("Link '%s' not found; navigating to fallback URL: %s", link_text, FALLBACK_URL)
        page.goto(FALLBACK_URL, wait_until="domcontentloaded", timeout=30000)

    browser_session["page"].wait_for_timeout(2000)


@when("selects the Name and County lookup criteria if present")
def select_lookup_criteria(browser_session):
    page = browser_session["page"]
    try:
        criteria_select = page.locator("select").first
        if criteria_select.count() > 0 and criteria_select.is_visible():
            for option_label in ["Name, County, Date of Birth", "Name"]:
                try:
                    criteria_select.select_option(label=option_label, timeout=3000)
                    logger.info("Selected lookup criteria: '%s'", option_label)
                    page.wait_for_timeout(1000)
                    break
                except PlaywrightError:
                    continue
    except Exception as e:
        logger.debug("Lookup criteria dropdown not applicable: %s", e)


@when("populates the voter lookup fields using the environment details")
def populate_voter_fields(browser_session, voter_env):
    page = browser_session["page"]

    field_mappings = [
        (
            "First Name",
            ["input[name*='firstName' i]", "input[id*='firstName' i]", "input[aria-label*='First Name' i]"],
            voter_env["first_name"],
        ),
        (
            "Last Name",
            ["input[name*='lastName' i]", "input[id*='lastName' i]", "input[aria-label*='Last Name' i]"],
            voter_env["last_name"],
        ),
        (
            "Zip Code",
            ["input[name*='zip' i]", "input[id*='zip' i]", "input[aria-label*='Zip' i]"],
            voter_env["zip_code"],
        ),
    ]

    for label, selectors, value in field_mappings:
        filled = False
        for selector in selectors:
            loc = page.locator(selector).first
            if loc.count() > 0 and loc.is_visible():
                loc.fill(value)
                logger.info("Populated %s via selector '%s'", label, selector)
                filled = True
                break
        if not filled:
            logger.warning("No visible input located for %s", label)

    # Populate or select COUNTY in ALL CAPS
    county_select = page.locator(
        "select[name*='county' i], select[id*='county' i], select[aria-label*='County' i]"
    ).first
    if county_select.count() > 0 and county_select.is_visible():
        try:
            county_select.select_option(label=voter_env["county"], timeout=5000)
            logger.info("Selected COUNTY='%s' from dropdown", voter_env["county"])
        except PlaywrightError as e:
            logger.warning("Could not select COUNTY='%s' by label: %s", voter_env["county"], e)
    else:
        county_input = page.locator(
            "input[name*='county' i], input[id*='county' i], input[aria-label*='County' i]"
        ).first
        if county_input.count() > 0 and county_input.is_visible():
            county_input.fill(voter_env["county"])
            logger.info("Filled COUNTY='%s' into input field", voter_env["county"])


@then("the COUNTY value should be formatted in ALL CAPS")
def verify_county_uppercase(voter_env):
    assert voter_env["county"].isupper(), f"Expected COUNTY in ALL CAPS, got: {voter_env['county']}"
    logger.info("Verified COUNTY='%s' is strictly uppercase.", voter_env["county"])


@then("a final verification screenshot is captured before closing the browser")
def final_review_and_screenshot(browser_session):
    page = browser_session["page"]
    if os.getenv("INTERACTIVE_PAUSE", "true").lower() == "true" and os.isatty(0):
        logger.info("Form populated. Complete any remaining fields in the browser window.")
        input("\nPress Enter in the terminal to capture the final review screenshot and finish the test...")
    capture_screenshot(page, "98_final_review_state")
