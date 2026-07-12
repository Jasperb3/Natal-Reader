from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import json
import os
import re
import subprocess
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime

# Constants
CHROME_BINARY_PATH = "/usr/bin/chromium-browser"
CHROMEDRIVER_PATH = "/usr/local/bin/chromedriver"
CHROME_FOR_TESTING_MILESTONES_URL = "https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone.json"
CHROME_FOR_TESTING_DOWNLOAD_URL = "https://storage.googleapis.com/chrome-for-testing-public/{version}/linux64/chromedriver-linux64.zip"


def _get_version_major(binary_path: str) -> str | None:
    """Runs `<binary> --version` and returns the major (milestone) version, or None if unavailable."""
    try:
        output = subprocess.run(
            [binary_path, "--version"], capture_output=True, text=True, timeout=10
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return None

    match = re.search(r"(\d+)\.\d+\.\d+\.\d+", output)
    return match.group(1) if match else None


def _ensure_chromedriver_matches_chrome():
    """Downloads a matching chromedriver build if it doesn't match the installed Chrome/Chromium major version."""
    chrome_major = _get_version_major(CHROME_BINARY_PATH)
    if chrome_major is None:
        print(f"Warning: could not determine Chrome version from {CHROME_BINARY_PATH}")
        return

    chromedriver_major = _get_version_major(CHROMEDRIVER_PATH)
    if chromedriver_major == chrome_major:
        return

    print(
        f"chromedriver version (milestone {chromedriver_major}) does not match "
        f"Chrome (milestone {chrome_major}); attempting to download a matching build..."
    )
    try:
        with urllib.request.urlopen(CHROME_FOR_TESTING_MILESTONES_URL, timeout=15) as response:
            milestones = json.load(response)["milestones"]

        milestone_info = milestones.get(chrome_major)
        if milestone_info is None:
            print(f"Warning: no known chromedriver build for Chrome milestone {chrome_major}")
            return

        full_version = milestone_info["version"]
        download_url = CHROME_FOR_TESTING_DOWNLOAD_URL.format(version=full_version)

        with tempfile.TemporaryDirectory() as tmp_dir:
            zip_path = os.path.join(tmp_dir, "chromedriver-linux64.zip")
            urllib.request.urlretrieve(download_url, zip_path)

            with zipfile.ZipFile(zip_path) as zip_file:
                zip_file.extract("chromedriver-linux64/chromedriver", tmp_dir)

            extracted_path = os.path.join(tmp_dir, "chromedriver-linux64", "chromedriver")
            with open(extracted_path, "rb") as extracted_file:
                new_binary = extracted_file.read()

            with open(CHROMEDRIVER_PATH, "wb") as driver_file:
                driver_file.write(new_binary)
            os.chmod(CHROMEDRIVER_PATH, 0o755)

        print(f"chromedriver updated to version {full_version}")
    except Exception as e:
        print(f"Warning: failed to update chromedriver automatically: {e}")


@contextmanager
def get_driver(window_size=(1920, 1080)):
    """Context manager for handling driver creation and cleanup"""
    _ensure_chromedriver_matches_chrome()

    chrome_options = Options()
    chrome_options.binary_location = CHROME_BINARY_PATH
    
    # Core options
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--remote-debugging-pipe')
    chrome_options.add_argument('--disable-gpu')
    
    # Additional stability options
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.add_argument('--disable-features=VizDisplayCompositor')
    
    # Create a temporary directory for Chrome
    tmp_dir = '/tmp/chrome-data'
    os.makedirs(tmp_dir, exist_ok=True)
    chrome_options.add_argument(f'--user-data-dir={tmp_dir}')
    
    service = Service(
        executable_path=CHROMEDRIVER_PATH,
        service_args=['--verbose', '--log-path=/tmp/chromedriver.log']
    )
    
    driver = None
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_window_size(*window_size)
        yield driver
    finally:
        if driver:
            try:
                driver.close()
                driver.quit()
            except Exception as e:
                print(f"Error during driver cleanup: {e}")
            try:
                import shutil
                shutil.rmtree(tmp_dir, ignore_errors=True)
            except Exception as e:
                print(f"Error cleaning up temp directory: {e}")


def capture_svg_screenshot(svg_path: str, output_dir: str = "./screenshots") -> str:
    """
    Opens an SVG file in a headless browser, takes a screenshot, and saves it.

    Args:
        svg_path (str): The file path to the SVG file.
        output_dir (str): Directory to save the screenshot. Defaults to "./screenshots".

    Returns:
        str: The file path of the saved screenshot.
    """
    # Validate the SVG file path
    if not os.path.exists(svg_path):
        raise FileNotFoundError(f"SVG file not found: {svg_path}")

    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Generate the screenshot file path
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = os.path.join(output_dir, f"svg_screenshot_{timestamp}.png")

    try:
        with get_driver() as driver:
            # Set higher DPR for better resolution
            driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
                'mobile': False,
                'width': 1920,
                'height': 1080,
                'deviceScaleFactor': 2.0  # This doubles the resolution
            })

            # Open the SVG file
            driver.get(f"file://{os.path.abspath(svg_path)}")

            # Wait for SVG to load and get its dimensions
            script = """
                return {
                    width: document.documentElement.getBoundingClientRect().width,
                    height: document.documentElement.getBoundingClientRect().height
                };
            """
            dimensions = driver.execute_script(script)
            
            # Set window size to match SVG dimensions with the scaling factor
            driver.set_window_size(
                int(dimensions['width'] * 2) + 40,  # Double the width + padding
                int(dimensions['height'] * 2) + 40  # Double the height + padding
            )

            # Save the screenshot
            driver.save_screenshot(screenshot_path)
            print(f"Screenshot saved to: {screenshot_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to capture SVG screenshot: {e}")

    return screenshot_path

if __name__ == "__main__":
    capture_svg_screenshot("/home/j/ai/crewAI/astro/natal_reader/natal_reader/tests/JohnDoeNatalChart.svg")
