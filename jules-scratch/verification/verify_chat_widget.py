from playwright.sync_api import sync_playwright, Page, expect

def verify_chat_widget(page: Page):
    """
    This script verifies that the new user chat widget can be opened.
    """
    # 1. Arrange: Go to the login page.
    page.goto("http://127.0.0.1:5000/login")

    # 2. Act: Log in as the admin user.
    page.get_by_label("Username").fill("admin")
    page.get_by_label("Password").fill("admin123")
    page.get_by_role("button", name="Sign In").click()

    # 3. Assert: Wait for the dashboard to load by checking for the correct heading.
    expect(page).to_have_url("http://127.0.0.1:5000/dashboard")
    expect(page.get_by_role("heading", name="Welcome, admin")).to_be_visible()

    # 4. Act: Click the chat toggle button.
    chat_toggle = page.locator("#chatToggle")
    expect(chat_toggle).to_be_visible()
    chat_toggle.click()

    # 5. Assert: Wait for the chat window to be visible.
    chat_window = page.locator(".chat-window")
    expect(chat_window).to_be_visible()

    # 6. Screenshot: Capture the final result for visual verification.
    page.screenshot(path="jules-scratch/verification/chat_widget.png")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        verify_chat_widget(page)
        browser.close()

if __name__ == "__main__":
    main()
