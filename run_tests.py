import sys
import subprocess


def bootstrap_and_run():
    """Ensures pytest, pytest-bdd, playwright, and python-dotenv are installed, then runs pytest."""
    required_packages = {
        "pytest": "pytest",
        "pytest_bdd": "pytest-bdd",
        "playwright": "playwright",
        "dotenv": "python-dotenv",
    }

    missing = []
    for mod, pkg in required_packages.items():
        try:
            __import__(mod)
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"Installing missing test dependencies: {', '.join(missing)}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])

    print("Ensuring Playwright Chromium binary is installed...")
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])

    print("\nRunning pytest-bdd suite...")
    # Pass '-s' so interactive terminal prompt works cleanly
    sys.exit(subprocess.call([sys.executable, "-m", "pytest", "-s", *sys.argv[1:]]))


if __name__ == "__main__":
    bootstrap_and_run()
