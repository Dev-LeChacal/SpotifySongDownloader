import os
import time
from typing import Optional, Callable
from selenium import webdriver
from selenium.common import (
    TimeoutException,
    ElementClickInterceptedException,
    NoSuchElementException,
)
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from mutagen.easyid3 import EasyID3
from history import add_entry

class Downloader:
    def __init__(self, download_directory: str = None, progress_callback: Optional[Callable] = None):
        self.song_url = None
        self.download_directory = download_directory
        self.progress_callback = progress_callback

        chrome_preferences = {
            "download.default_directory": self.download_directory,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "profile.managed_default_content_settings.images": 2,
        }

        chrome_options = Options()
        chrome_options.add_experimental_option("prefs", chrome_preferences)
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.page_load_strategy = "eager"

        self.driver = webdriver.Chrome(service=ChromeService(), options=chrome_options)
        self.driver.set_page_load_timeout(30)

    def _update_progress(self, message: str, progress: float = None, status: str = "info"):
        if self.progress_callback:
            self.progress_callback({
                "message": message,
                "progress": progress,
                "status": status,
            })

    def _accept_consent_if_present(self):
        try:
            self._update_progress("Locating consent button...", 0.1)
            button = WebDriverWait(self.driver, 5).until(
                ec.element_to_be_clickable(
                    (By.XPATH, '//button[contains(@class, "fc-button") and .//p[text()="Consent"]]')
                )
            )
            button.click()
            self._update_progress("Consent accepted", 0.15)
        except (TimeoutException, ElementClickInterceptedException, NoSuchElementException):
            self._update_progress("Consent button not found", 0.15)

    def download_from_url(self, song_url: str):
        self.song_url = song_url
        self._update_progress("Opening downloader site...", 0.0)
        try:
            self.driver.get("https://spotidown.app")
        except TimeoutException:
            self._update_progress("Failed to load initial page", 0.0, "error")
            return

        self._accept_consent_if_present()

        self._update_progress("Locating URL input field...", 0.2)
        try:
            url_input = WebDriverWait(self.driver, 5).until(
                ec.visibility_of_element_located((By.ID, "url"))
            )
        except TimeoutException:
            self._update_progress("URL input field not found", 0.2, "error")
            return

        url_input.clear()
        url_input.send_keys(song_url)

        self._update_progress("Submitting URL...", 0.3)
        try:
            send_button = WebDriverWait(self.driver, 5).until(
                ec.element_to_be_clickable((By.ID, "send"))
            )
            send_button.click()
        except TimeoutException:
            self._update_progress("Send button not found", 0.3, "error")
            return

        self._update_progress("Locating download button...", 0.4)
        try:
            download_button = WebDriverWait(self.driver, 5).until(
                ec.element_to_be_clickable((By.XPATH, '//button[contains(.,"Download MP3")]'))
            )
            download_button.click()
        except TimeoutException:
            self._update_progress("Download MP3 button not found", 0.4, "error")
            return

        self._update_progress("Locating download link...", 0.5)
        try:
            download_link = WebDriverWait(self.driver, 5).until(
                ec.presence_of_element_located(
                    (By.XPATH, '//a[contains(@class,"abutton") and contains(.,"Download Mp3")]')
                )
            )
            download_url = download_link.get_attribute("href")
        except TimeoutException:
            self._update_progress("Download link not found", 0.5, "error")
            return

        self._update_progress("Starting file download...", 0.6)
        try:
            self.driver.get(download_url)
        except TimeoutException:
            self._update_progress("Failed to initiate download", 0.6, "error")
            return

        time.sleep(1)

    def wait_for_download_completion(self, timeout: int = 60, estimated_size: Optional[int] = None):
        self._update_progress("Waiting for download to finish...", 0.65)
        start_time = time.time()
        end_time = start_time + timeout

        previous_size = None
        previous_time = None

        while time.time() < end_time:
            files = os.listdir(self.download_directory)
            temp_files = [f for f in files if f.lower().endswith(".crdownload")]

            if not temp_files:
                mp3_files = [f for f in files if f.lower().endswith(".mp3")]
                if mp3_files:
                    self._update_progress("Download completed successfully!", 1.0, "success")
                    for file in mp3_files:
                        if file.startswith("SpotiDown.App - "):
                            old_path = os.path.join(self.download_directory, file)
                            clean_name = file.replace("SpotiDown.App - ", "")
                            new_path = os.path.join(self.download_directory, clean_name)

                            try:
                                audio = EasyID3(old_path)
                                artist = audio.get('artist', [''])[0]
                                title = audio.get('title', [''])[0]
                            except KeyError:
                                filename_without_ext = os.path.splitext(clean_name)[0]
                                if " - " in filename_without_ext:
                                    artist, title = filename_without_ext.split(" - ", 1)
                                else:
                                    artist, title = "", filename_without_ext

                            add_entry(title, artist, self.song_url, new_path)

                            os.rename(old_path, new_path)
                    return

            if temp_files:
                temp_file = temp_files[0]
                temp_path = os.path.join(self.download_directory, temp_file)
                current_size = os.path.getsize(temp_path)
                current_time = time.time()

                if previous_size is not None and current_time > previous_time:
                    bytes_delta = current_size - previous_size
                    time_delta = current_time - previous_time

                    if bytes_delta > 0:
                        speed = bytes_delta / time_delta
                        if estimated_size:
                            remaining = estimated_size - current_size
                            eta = remaining / speed if speed > 0 else None
                            progress = min(0.65 + (current_size / estimated_size) * 0.35, 0.99)
                            if eta is not None:
                                message = (
                                    f"Downloaded {current_size / 1e6:.2f} MB, "
                                    f"Speed {speed / 1e3:.2f} KB/s, ETA {eta:.1f}s"
                                )
                            else:
                                message = f"Downloaded {current_size / 1e6:.2f} MB, Speed {speed / 1e3:.2f} KB/s"
                        else:
                            progress = min(0.65 + (current_size / 10e6) * 0.25, 0.90)
                            message = f"Downloaded {current_size / 1e6:.2f} MB, Speed {speed / 1e3:.2f} KB/s"

                        self._update_progress(message, progress)
                    else:
                        progress = min(0.65 + (current_size / 10e6) * 0.25, 0.90)
                        self._update_progress(f"Downloaded {current_size / 1e6:.2f} MB (waiting...)", progress)

                previous_size = current_size
                previous_time = current_time
            else:
                self._update_progress("Searching for temporary download file...", 0.65)

            time.sleep(0.5)

        self._update_progress("Download did not complete within the time limit", 0.9, "error")

    def close(self):
        self.driver.quit()