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
