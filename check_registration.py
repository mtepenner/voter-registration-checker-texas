import os
import sys
import subprocess


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
        print(f"Installing missing Python packages: {', '.join(missing_packages)}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_packages])

    # Ensure Playwright's Chromium binary is installed
    print("Ensuring Playwright Chromium browser is installed...")
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])


ensure_dependencies()

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


def load_voter_env():
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
        print(f"Error: Missing required environment variables in .env: {', '.join(missing)}")
        print("Copy .env.example to .env and fill in your information before running.")
        sys.exit(1)

    return {
        "first_name": first_name,
        "last_name": last_name,
        "zip_code": zip_code,
        "county": county,
    }


def check_voter_registration():
    voter = load_voter_env()
    start_url = "https://www.votetexas.gov/register-to-vote/index.html"

    with sync_playwright() as p:
        # Launch visible browser so you can review the official portal results directly
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print(f"Navigating to {start_url}...")
        page.goto(start_url, wait_until="domcontentloaded")

        # Locate the official 'Am I Registered?' link on VoteTexas.gov
        portal_link = page.locator("a", has_text="Am I Registered").first
        target_page = page

        if portal_link.count() > 0:
            href = portal_link.get_attribute("href")
            print(f"Found official 'Am I Registered?' portal link: {href}")
            with context.expect_page() as new_page_info:
                portal_link.click()
            try:
                target_page = new_page_info.value
                target_page.wait_for_load_state("domcontentloaded")
            except PlaywrightTimeoutError:
                # Link opened in the same tab
                target_page = page
                target_page.wait_for_load_state("domcontentloaded")
        else:
            # Fallback to the official Texas SOS My Voter Portal linked by VoteTexas.gov
            fallback_url = "https://teamrv-mvp.sos.texas.gov/MVP/voterDetails.do"
            print(f"Navigating directly to official voter portal: {fallback_url}")
            target_page.goto(fallback_url, wait_until="domcontentloaded")

        target_page.wait_for_timeout(2000)

        # If the portal offers a Selection Criteria dropdown (e.g., Name, County, Date of Birth)
        try:
            criteria_select = target_page.locator("select").first
            if criteria_select.is_visible():
                for option_label in ["Name, County, Date of Birth", "Name"]:
                    try:
                        criteria_select.select_option(label=option_label)
                        break
                    except Exception:
                        continue
        except Exception:
            pass

        # Populate First Name, Last Name, County (in ALL CAPS), and Zip Code
        field_mappings = [
            (["input[name*='firstName' i]", "input[id*='firstName' i]", "input[aria-label*='First Name' i]"], voter["first_name"]),
            (["input[name*='lastName' i]", "input[id*='lastName' i]", "input[aria-label*='Last Name' i]"], voter["last_name"]),
            (["input[name*='zip' i]", "input[id*='zip' i]", "input[aria-label*='Zip' i]"], voter["zip_code"]),
        ]

        for selectors, value in field_mappings:
            for selector in selectors:
                loc = target_page.locator(selector).first
                if loc.count() > 0 and loc.is_visible():
                    loc.fill(value)
                    break

        # Select or fill COUNTY in ALL CAPS
        county_select = target_page.locator("select[name*='county' i], select[id*='county' i], select[aria-label*='County' i]").first
        if county_select.count() > 0 and county_select.is_visible():
            try:
                county_select.select_option(label=voter["county"])
            except Exception:
                pass
        else:
            county_input = target_page.locator("input[name*='county' i], input[id*='county' i], input[aria-label*='County' i]").first
            if county_input.count() > 0 and county_input.is_visible():
                county_input.fill(voter["county"])

        print("\nForm fields populated for:")
        print(f"  First Name : {voter['first_name']}")
        print(f"  Last Name  : {voter['last_name']}")
        print(f"  County     : {voter['county']}")
        print(f"  Zip Code   : {voter['zip_code']}")
        print("\nComplete any remaining required fields in the open browser window and submit to verify your official status.")

        input("Press Enter in this terminal when you are finished to close the browser...")
        browser.close()


if __name__ == "__main__":
    check_voter_registration()
