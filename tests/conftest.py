import os
import re
import logging
from datetime import datetime
from pathlib import Path
import pytest
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page, Error as PlaywrightError

logger = logging.getLogger(__name__)

ARTIFACTS_DIR = Path("artifacts")
LOG_DIR = ARTIFACTS_DIR / "logs"
SCREENSHOT_DIR = ARTIFACTS_DIR / "screenshots"

LOG_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def capture_screenshot(page: Page | None, label: str) -> Path | None:
    """Captures a sanitized, timestamped full-page screenshot."""
    if not page or page.is_closed():
        logger.warning("Skipped screenshot '%s': page is closed or unavailable.", label)
        return None

    safe_label = re.sub(r"[^a-zA-Z0-9_-]+", "_", label).strip("_").lower()[:50]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = SCREENSHOT_DIR / f"{timestamp}_{safe_label}.png"

    try:
        page.screenshot(path=str(filepath), full_page=True)
        logger.info("Screenshot saved: %s", filepath)
        return filepath
    except PlaywrightError as e:
        logger.error("Failed to capture screenshot '%s': %s", label, e, exc_info=True)
        return None


@pytest.fixture(scope="session")
def voter_env() -> dict:
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
        pytest.fail(
            f"Missing required environment variables in .env: {', '.join(missing)}. "
            "Copy .env.example to .env and fill in your details."
        )

    return {
        "first_name": first_name,
        "last_name": last_name,
        "zip_code": zip_code,
        "county": county,
    }


@pytest.fixture(scope="function")
def browser_session():
    """Provides a mutable dict holding browser, context, and the currently active page tab."""
    with sync_playwright() as p:
        logger.info("Launching Chromium browser session...")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()
        page.on("pageerror", lambda err: logger.debug("Uncaught page error: %s", err))

        state = {
            "browser": browser,
            "context": context,
            "page": page,
            "step_counter": 0,
        }

        yield state

        logger.info("Closing Chromium browser session...")
        browser.close()


# --- pytest-bdd Hooks for Automatic Step & Error Screenshots ---
def pytest_bdd_after_step(request, feature, scenario, step, step_func, step_func_args):
    """Automatically captures a milestone screenshot after each successful BDD step."""
    if "browser_session" in request.fixturenames:
        session = request.getfixturevalue("browser_session")
        session["step_counter"] += 1
        step_label = f"{session['step_counter']:02d}_{step.keyword}_{step.name}"
        capture_screenshot(session.get("page"), step_label)


def pytest_bdd_step_error(request, feature, scenario, step, step_func, step_func_args, exception):
    """Logs full traceback and captures an error screenshot if any BDD step fails."""
    logger.error(
        "Step failed: '%s %s' | Exception: %s",
        step.keyword,
        step.name,
        exception,
        exc_info=True,
    )
    if "browser_session" in request.fixturenames:
        session = request.getfixturevalue("browser_session")
        error_label = f"99_ERROR_{step.keyword}_{step.name}"
        capture_screenshot(session.get("page"), error_label)
