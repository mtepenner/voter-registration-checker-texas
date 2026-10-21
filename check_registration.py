import os
import sys
import logging
import subprocess
from datetime import datetime
from pathlib import Path

# --- 1. Setup Artifacts Directories & Logging ---
ARTIFACTS_DIR = Path("artifacts")
LOG_DIR = ARTIFACTS_DIR / "logs"
SCREENSHOT_DIR = ARTIFACTS_DIR / "screenshots"

LOG_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "voter_check.log"

logger = logging.getLogger("VoterCheckAutomation")
logger.setLevel(logging.DEBUG)

# File handler (captures DEBUG and full tracebacks)
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(
    "%(asctime)s | %(levelname)-8s | %(funcName)s:%(lineno)d | %(message)s"
)
file_handler.setFormatter(file_formatter)

# Console handler (clean INFO output)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s", "%H:%M:%S")
console_handler.setFormatter(console_formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)


# --- 2. Self-Bootstrapping Dependencies ---
def ensure_dependencies():
    """Automatically downloads and installs required Python packages and Playwright browsers."""
    required_packages = {
        "playwright": "playwright",
        "dotenv": "python-dotenv",
    }

    missing_packages = []
    for module_name, pip_name in required_packages.items():
        try:
            __import__(module_name)
        except ImportError:
            missing_packages.append(pip_name)

    if missing_packages:
        logger.info("Installing missing Python packages: %s", ", ".join(missing_packages))
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_packages])
        except subprocess.CalledProcessError as e:
            logger.critical("Failed to install Python dependencies: %s", e, exc_info=True)
            sys.exit(1)

    logger.info("Verifying Playwright Chromium browser installation...")
    try:
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    except subprocess.CalledProcessError as e:
        logger.critical("Failed to install Playwright Chromium binary: %s", e, exc_info=True)
        sys.exit(1)


ensure_dependencies()

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page, Error as PlaywrightError, TimeoutError as PlaywrightTimeoutError


# --- 3. Helper Functions ---
def take_screenshot(page: Page, step_name: str) -> Path | None:
    """Captures a timestamped full-page screenshot and logs the output file path."""
    if not page or page.is_closed():
        logger.warning("Cannot capture screenshot for '%s': page is closed or unavailable.", step_name)
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{step_name}.png"
    filepath = SCREENSHOT_DIR / filename

    try:
        page.screenshot(path=str(filepath), full_page=True)
        logger.info("Saved screenshot: %s", filepath)
        return filepath
    except PlaywrightError as e:
        logger.error("Failed to capture screenshot '%s': %s", step_name, e, exc_info=True)
        return None


def load_voter_env() -> dict:
    """Loads voter lookup details from .env and enforces ALL CAPS on COUNTY."""
    load_dotenv()

    first_name = os.getenv("FIRST_NAME", "").strip()
    last_name = os.getenv("LAST_NAME", "").strip()
    zip_code = os.getenv("ZIP_CODE", "").strip()
    county = os.getenv("COUNTY", "").strip().upper()

    missing = [
        key
        for key, val in [
            ("FIRST_NAME", first_name),
            ("LAST_NAME", last_name),
            ("ZIP_CODE", zip_code),
            ("COUNTY", county),
        ]
        if not val
    ]

    if missing:
        logger.critical(
            "Missing required environment variables in .env: %s. "
            "Copy .env.example to .env and fill in your values.",
            ", ".join(missing),
        )
        sys.exit(1)

    logger.debug(
        "Loaded voter configuration: FIRST_NAME=%s, LAST_NAME=%s, COUNTY=%s, ZIP_CODE=%s",
        first_name,
        last_name,
        county,
        zip_code,
    )

    return {
        "first_name": first_name,
        "last_name": last_name,
        "zip_code": zip_code,
        "county": county,
    }


# --- 4. Main Automation Flow ---
def check_voter_registration():
    voter = load_voter_env()
    start_url = "https://www.votetexas.gov/register-to-vote/index.html"
    fallback_url = "https://teamrv-mvp.sos.texas.gov/MVP/voterDetails.do"

    with sync_playwright() as p:
        browser = None
        active_page = None

        try:
            logger.info("Launching Chromium browser...")
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(viewport={"width": 1280, "height": 900})
            active_page = context.new_page()

            # Listen for uncaught page errors and log them at DEBUG level
            active_page.on("pageerror", lambda err: logger.debug("Browser page error: %s", err))

            logger.info("Navigating to %s", start_url)
            active_page.goto(start_url, wait_until="domcontentloaded", timeout=30000)
            take_screenshot(active_page, "01_votetexas_landing")

            # Locate the 'Am I Registered?' link on VoteTexas.gov
            portal_link = active_page.locator("a", has_text="Am I Registered").first

            if portal_link.count() > 0:
                href = portal_link.get_attribute("href")
                logger.info("Found 'Am I Registered?' portal link (%s). Clicking...", href)
                try:
                    with context.expect_page(timeout=10000) as new_page_info:
                        portal_link.click()
                    active_page = new_page_info.value
                    active_page.wait_for_load_state("domcontentloaded", timeout=30000)
                    logger.info("Switched to newly opened portal tab: %s", active_page.url)
                except PlaywrightTimeoutError:
                    logger.debug("Portal opened in the same tab or popup timed out; checking current page.")
                    active_page.wait_for_load_state("domcontentloaded", timeout=15000)
            else:
                logger.warning(
                    "'Am I Registered?' link not found on landing page. Navigating directly to fallback: %s",
                    fallback_url,
                )
                active_page.goto(fallback_url, wait_until="domcontentloaded", timeout=30000)

            active_page.wait_for_timeout(2000)
            take_screenshot(active_page, "02_voter_portal_loaded")

            # Select lookup criteria dropdown if present
            try:
                criteria_select = active_page.locator("select").first
                if criteria_select.count() > 0 and criteria_select.is_visible():
                    for option_label in ["Name, County, Date of Birth", "Name"]:
                        try:
                            criteria_select.select_option(label=option_label, timeout=3000)
                            logger.info("Selected lookup criteria option: '%s'", option_label)
                            active_page.wait_for_timeout(1000)
                            break
                        except PlaywrightError:
                            continue
            except Exception as e:
                logger.debug("Criteria dropdown selection skipped: %s", e)

            # Populate text input fields
            field_mappings = [
                (
                    "First Name",
                    ["input[name*='firstName' i]", "input[id*='firstName' i]", "input[aria-label*='First Name' i]"],
                    voter["first_name"],
                ),
                (
                    "Last Name",
                    ["input[name*='lastName' i]", "input[id*='lastName' i]", "input[aria-label*='Last Name' i]"],
                    voter["last_name"],
                ),
                (
                    "Zip Code",
                    ["input[name*='zip' i]", "input[id*='zip' i]", "input[aria-label*='Zip' i]"],
                    voter["zip_code"],
                ),
            ]

            for field_label, selectors, value in field_mappings:
                populated = False
                for selector in selectors:
                    loc = active_page.locator(selector).first
                    if loc.count() > 0 and loc.is_visible():
                        loc.fill(value)
                        logger.info("Populated %s using selector '%s'", field_label, selector)
                        populated = True
                        break
                if not populated:
                    logger.warning("Could not locate a visible input field for %s", field_label)

            # Populate or select COUNTY (enforced ALL CAPS)
            county_select = active_page.locator(
                "select[name*='county' i], select[id*='county' i], select[aria-label*='County' i]"
            ).first
            if county_select.count() > 0 and county_select.is_visible():
                try:
                    county_select.select_option(label=voter["county"], timeout=5000)
                    logger.info("Selected COUNTY='%s' from dropdown.", voter["county"])
                except PlaywrightError as e:
                    logger.warning("Failed to select COUNTY='%s' by exact label: %s", voter["county"], e)
            else:
                county_input = active_page.locator(
                    "input[name*='county' i], input[id*='county' i], input[aria-label*='County' i]"
                ).first
                if county_input.count() > 0 and county_input.is_visible():
                    county_input.fill(voter["county"])
                    logger.info("Filled COUNTY='%s' into text input.", voter["county"])
                else:
                    logger.warning("Could not locate a visible County dropdown or input field.")

            # Capture screenshot of populated form
            take_screenshot(active_page, "03_form_populated")

            logger.info(
                "Form population complete. Complete any remaining required fields (such as Date of Birth) "
                "and submit in the open browser window."
            )
            input("\nPress Enter in this terminal to capture a final screenshot and close the browser...")

            take_screenshot(active_page, "04_final_review")

        except PlaywrightTimeoutError as e:
            logger.error("Navigation or element timeout occurred: %s", e, exc_info=True)
            take_screenshot(active_page, "99_timeout_error")
        except Exception as e:
            logger.error("Unexpected error during voter registration check: %s", e, exc_info=True)
            take_screenshot(active_page, "99_unexpected_error")
        finally:
            if browser:
                logger.info("Closing browser session. Full logs available at %s", LOG_FILE)
                browser.close()


if __name__ == "__main__":
    check_voter_registration()
