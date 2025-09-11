import re
import random
import string
from playwright.sync_api import sync_playwright, Page, expect

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # --- Step 1: Create a new user ---
    print("Step 1: Creating a new user...")
    page.goto("http://127.0.0.1:5000/signup")

    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    test_username = f"testuser_{random_suffix}"
    test_password = "Password123!"

    page.get_by_label("Username").fill(test_username)
    page.get_by_label("Password", exact=True).fill(test_password)
    page.get_by_label("Confirm Password").fill(test_password)
    page.get_by_role("button", name="Create My Account").click()
    expect(page.get_by_text("Account created successfully!")).to_be_visible()
    print(f"User '{test_username}' created.")

    # --- Step 2: Log in as admin and deactivate the user ---
    print("Step 2: Logging in as admin to deactivate user...")
    page.goto("http://127.0.0.1:5000/login")
    page.get_by_label("Username").fill("admin")
    page.get_by_label("Password").fill("admin123")
    page.get_by_role("button", name="Sign In").click()
    expect(page.get_by_role("heading", name="Welcome, admin")).to_be_visible()
    print("Admin logged in.")

    page.goto("http://127.0.0.1:5000/admin")

    page.on("dialog", lambda dialog: dialog.accept())

    user_row = page.locator(f"tr:has-text('{test_username}')")

    # --- Deactivate User ---
    print("Deactivating user...")
    deactivate_button = user_row.get_by_role("button", name="Deactivate")
    deactivate_button.click()
    page.wait_for_load_state("networkidle")
    expect(page.get_by_text(f"Customer '{test_username}' has been deactivated.")).to_be_visible()
    print("User deactivated.")

    # --- Verify 'Activate' button is visible ---
    print("Verifying 'Activate' button is visible...")
    activate_button = user_row.get_by_role("button", name="Activate")
    expect(activate_button).to_be_visible()
    print("'Activate' button is visible.")

    # --- Activate User ---
    print("Activating user...")
    activate_button.click()
    page.wait_for_load_state("networkidle")
    expect(page.get_by_text(f"Customer '{test_username}' has been activated.")).to_be_visible()
    print("User activated.")

    # --- Verify 'Deactivate' button is visible again ---
    print("Verifying 'Deactivate' button is visible again...")
    deactivate_button = user_row.get_by_role("button", name="Deactivate")
    expect(deactivate_button).to_be_visible()
    print("'Deactivate' button is visible again.")

    print("Taking final screenshot...")
    page.screenshot(path="jules-scratch/verification/reactivation_flow.png")

    # --- Cleanup ---
    browser.close()

if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)
