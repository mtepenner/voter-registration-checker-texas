# Texas Voter Registration Lookup Automation

A self-bootstrapping Python automation script built with **Playwright** that navigates to [VoteTexas.gov](https://www.votetexas.gov/register-to-vote/index.html), transitions to the official Texas Secretary of State **Am I Registered?** lookup portal, and populates your voter lookup fields automatically from a local `.env` file.

## Features

* **Zero-Config Bootstrapping:** Automatically detects and installs missing Python dependencies (`playwright`, `python-dotenv`) and the Playwright Chromium binary on first run.
* **Environment-Driven Privacy:** Loads `FIRST_NAME`, `LAST_NAME`, `ZIP_CODE`, and `COUNTY` (automatically normalized to `ALL CAPS`) from a local `.env` file excluded from Git.
* **Milestone & Failure Screenshots:** Captures timestamped, full-page PNG screenshots at each navigation step and automatically snapshots the DOM state if a timeout or unexpected exception occurs.
* **Dual-Target Logging:** Streams concise `INFO` status updates to the console while writing detailed `DEBUG` events and stack traces to `artifacts/logs/voter_check.log`.

## Prerequisites

* **Python 3.10+** installed and added to your system `PATH`.

## Quick Start

### 1. Configure Environment Variables

Copy the example environment template to a local `.env` file:

```bash
cp .env.example .env

```

Open `.env` and enter your lookup information (ensure `COUNTY` is in all caps):

```ini
FIRST_NAME=JANE
LAST_NAME=DOE
ZIP_CODE=78701
COUNTY=TRAVIS

```

### 2. Run the Script

Execute the script directly—it will install `playwright`, `python-dotenv`, and the Chromium browser binary automatically if they are not already present:

```bash
python check_registration.py

```

### 3. Review & Submit

1. The script launches a visible Chromium window, navigates through VoteTexas.gov to the Texas Secretary of State lookup portal, and fills in your configured details.
2. Complete any remaining required verification fields (such as Date of Birth) in the open browser window and submit the form.
3. Return to your terminal and press **Enter** to capture a final review screenshot and close the browser session cleanly.

## Project Structure & Artifacts

```text
.
├── .env.example             # Template for required environment variables
├── .gitignore               # Excludes .env and artifacts/ from version control
├── README.md                # Project documentation
├── check_registration.py    # Main self-bootstrapping Playwright script
└── artifacts/               # Auto-generated at runtime (git-ignored)
    ├── logs/
    │   └── voter_check.log
    └── screenshots/
        ├── YYYYMMDD_HHMMSS_01_votetexas_landing.png
        ├── YYYYMMDD_HHMMSS_02_voter_portal_loaded.png
        ├── YYYYMMDD_HHMMSS_03_form_populated.png
        └── YYYYMMDD_HHMMSS_04_final_review.png

```
