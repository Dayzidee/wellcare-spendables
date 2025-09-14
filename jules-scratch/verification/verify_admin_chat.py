from playwright.sync_api import sync_playwright, Page, expect

def verify_admin_chat_desktop(page: Page):
    """
    This script verifies that the admin chat dashboard loads correctly on desktop.
    """
    # 1. Arrange: Go to the login page.
    page.goto("http://127.0.0.1:5000/login")

    # 2. Act: Log in as the admin user.
    page.get_by_label("Username").fill("admin")
    page.get_by_label("Password").fill("admin123")
    page.get_by_role("button", name="Sign In").click()

    # 3. Act: Navigate to the admin chat page.
    page.goto("http://127.0.0.1:5000/admin/chat")

    # 4. Assert: Check for key elements on the new admin chat page.
    expect(page.get_by_role("heading", name="Support Chat Dashboard")).to_be_visible()

    # 5. Act: Manually execute the JS to show the active chat screen.
    page.evaluate("""
        const welcomeScreen = document.getElementById('chatWelcomeScreen');
        const activeScreen = document.getElementById('chatActiveScreen');
        if (welcomeScreen) {
            welcomeScreen.style.display = 'none';
        }
        if (activeScreen) {
            activeScreen.classList.remove('hidden');
        }
    """)

    # 6. Screenshot: Capture the final result for visual verification.
    page.screenshot(path="jules-scratch/verification/admin_chat_desktop_final.png")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        verify_admin_chat_desktop(page)
        browser.close()

if __name__ == "__main__":
    main()
