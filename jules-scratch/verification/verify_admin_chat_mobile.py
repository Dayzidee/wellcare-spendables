from playwright.sync_api import sync_playwright, Page, expect

def verify_admin_chat_mobile_interaction(page: Page):
    """
    This script verifies the interactivity of the mobile admin chat dashboard.
    """
    # 1. Arrange: Go to the login page.
    page.goto("http://127.0.0.1:5000/login")

    # 2. Act: Log in as the admin user.
    page.get_by_label("Username").fill("admin")
    page.get_by_label("Password").fill("admin123")
    page.get_by_role("button", name="Sign In").click()

    # 3. Act: Navigate to the admin chat page.
    page.goto("http://127.0.0.1:5000/admin/chat")

    # 4. Assert: Check for the sidebar toggle button.
    sidebar_toggle = page.locator("#sidebar-toggle")
    expect(sidebar_toggle).to_be_visible()

    # 5. Act: Click the sidebar toggle button.
    sidebar_toggle.click()

    # 6. Assert: Check if the sidebar is now active.
    sidebar = page.locator(".admin-chat-sidebar")
    expect(sidebar).to_have_class("admin-chat-sidebar active")

    # 7. Screenshot: Capture the view after the interaction.
    page.screenshot(path="jules-scratch/verification/admin_chat_mobile_interactive.png")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Manually set a mobile viewport.
        context = browser.new_context(
            viewport={'width': 414, 'height': 896},
            user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 13_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Mobile/15E148 Safari/604.1',
            is_mobile=True,
            has_touch=True,
        )
        page = context.new_page()

        verify_admin_chat_mobile_interaction(page)

        context.close()
        browser.close()

if __name__ == "__main__":
    main()
