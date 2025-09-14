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
    deactivate_button = user_row.get_by_role("button", name="Deactivate")
    deactivate_button.click()

    page.wait_for_load_state("networkidle")

    expect(page.get_by_text(f"Customer '{test_username}' has been deactivated.")).to_be_visible()
    print("User deactivated.")

    # --- Step 3: Log out as admin ---
    print("Step 3: Logging out as admin...")
    page.get_by_role("link", name="Logout").click()
    expect(page.get_by_text("You have been logged out.")).to_be_visible()
    print("Admin logged out.")

    # --- Step 4: Log in as the deactivated user ---
    print("Step 4: Logging in as deactivated user...")
    page.goto("http://127.0.0.1:5000/login")
    page.get_by_label("Username").fill(test_username)
    page.get_by_label("Password").fill(test_password)
    page.get_by_role("button", name="Sign In").click()

    # --- Step 5: Verify dashboard and modal ---
    print("Step 5: Verifying dashboard and modal...")
    # Ensure we are on the dashboard and not redirected
    expect(page).to_have_url("http://127.0.0.1:5000/dashboard")
    expect(page.get_by_role("heading", name=f"Welcome, {test_username}")).to_be_visible()
    print("Successfully loaded dashboard.")

    modal = page.locator("#deactivated-modal")
    expect(modal).to_be_visible()
    expect(modal.get_by_role("heading", name="Account Deactivated")).to_be_visible()
    print("Deactivation modal is visible.")

    print("Taking final screenshot...")
    page.screenshot(path="jules-scratch/verification/final_verification.png")

    # --- Cleanup ---
    browser.close()

if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)
