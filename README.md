# Texas Voter Registration Lookup Automation (Playwright + pytest-bdd)

A self-bootstrapping Behavior-Driven Development (**BDD**) automation suite built with **Python**, **Playwright**, and **pytest-bdd**. It navigates to [VoteTexas.gov](https://www.votetexas.gov/register-to-vote/index.html), follows the official Texas Secretary of State **Am I Registered?** portal link, and populates your voter lookup fields using credentials stored in a local `.env` file.

## Features

* **Zero-Config Bootstrapping:** Running `python run_tests.py` automatically detects and installs missing Python packages (`pytest`, `pytest-bdd`, `playwright`, `python-dotenv`) and the Playwright Chromium browser binary.
* **BDD Gherkin Architecture:** Separates human-readable behavior specifications (`features/voter_registration.feature`) from Playwright step definitions (`tests/test_voter_registration.py`) and session fixtures (`tests/conftest.py`).
* **Environment-Driven Privacy:** Loads `FIRST_NAME`, `LAST_NAME`, `ZIP_CODE`, and `COUNTY` (automatically normalized and asserted as `ALL CAPS`) from a git-ignored `.env` file.
* **Automated Step & Error Screenshots:** Uses `pytest_bdd_after_step` and `pytest_bdd_step_error` hooks to capture full-page, timestamped PNG screenshots after every Gherkin step and immediately upon any step failure.
* **Dual-Target Pytest Logging:** Configured via `pytest.ini` to stream concise `INFO` updates to the terminal while recording detailed `DEBUG` events and stack traces to `artifacts/logs/voter_check.log`.

## Prerequisites

* **Python 3.10+** installed and added to your system `PATH`.

## Quick Start

### 1. Configure Environment Variables

Copy the example environment template to a local `.env` file:

```bash
cp .env.example .env
```

Open `.env` and fill in your voter lookup details (`COUNTY` should be in all caps):

```ini
FIRST_NAME=JANE
LAST_NAME=DOE
ZIP_CODE=78701
COUNTY=TRAVIS
```

### 2. Run the BDD Test Suite

Run the self-bootstrapping test runner—it installs any missing dependencies and launches the `pytest-bdd` suite in interactive mode:

```bash
python run_tests.py
```

*(Once dependencies are installed, you can also run `pytest -s` directly, or run `INTERACTIVE_PAUSE=false python run_tests.py` to skip the terminal pause at the end of the scenario.)*

### 3. Review & Submit

1. The suite launches a visible Chromium window, navigates through VoteTexas.gov to the official Texas Secretary of State lookup portal, and populates your `.env` details.
2. Complete any remaining required verification fields (such as Date of Birth) in the open browser window and submit the form.
3. Return to your terminal and press **Enter** to capture the final review screenshot and close the browser session cleanly.

## Project Structure & Artifacts

```text
.
├── .env.example                        # Template for required environment variables
├── .gitignore                          # Excludes .env, caches, and artifacts/ from Git
├── README.md                           # Project documentation
├── pytest.ini                          # Pytest & dual-target logging configuration
├── run_tests.py                        # Self-bootstrapping test runner
├── features/
│   └── voter_registration.feature      # Gherkin BDD feature and scenario specification
├── tests/
│   ├── conftest.py                     # Playwright fixtures, .env loader, and BDD hooks
│   └── test_voter_registration.py      # Step definitions for voter lookup workflow
└── artifacts/                          # Auto-generated at runtime (git-ignored)
    ├── logs/
    │   └── voter_check.log             # Detailed DEBUG execution and error log
    └── screenshots/                    # Timestamped step, review, and error PNGs
        ├── YYYYMMDD_HHMMSS_01_given_valid_voter_details_are_loaded.png
        ├── YYYYMMDD_HHMMSS_02_given_the_browser_is_on_the_votetexas.png
        ├── YYYYMMDD_HHMMSS_03_when_the_user_follows_the_am_i_registered.png
        └── YYYYMMDD_HHMMSS_98_final_review_state.png
```
