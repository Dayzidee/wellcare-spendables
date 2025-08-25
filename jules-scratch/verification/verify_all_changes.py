import re
from playwright.sync_api import sync_playwright, Page, expect

BASE_URL = "http://127.0.0.1:5000"

def test_homepage_content_and_responsiveness(page: Page):
    """
    Verify new homepage sections and responsive button layout.
    """
    print("Navigating to homepage...")
    page.goto(BASE_URL)

    # 1. Verify new sections on desktop
    print("Checking for new sections on desktop...")
    expect(page.get_by_role("heading", name="Your Security is Our Priority")).to_be_visible()
    expect(page.get_by_role("heading", name="Frequently Asked Questions")).to_be_visible()
    page.screenshot(path="jules-scratch/verification/01_homepage_desktop_new_sections.png")
    print("Desktop homepage screenshot captured.")

    # 2. Verify responsive hero buttons on mobile
    print("Setting mobile viewport...")
    page.set_viewport_size({"width": 375, "height": 667})

    # The buttons are inside a div with class 'hero-buttons'
    hero_buttons = page.locator(".hero-buttons")
    expect(hero_buttons).to_have_css("flex-direction", "column")
    print("Verified hero buttons are stacked vertically.")

    page.screenshot(path="jules-scratch/verification/02_homepage_mobile_hero_buttons.png")
    print("Mobile homepage screenshot captured.")

def test_mobile_navigation_panel(page: Page):
    """
    Verify the new slide-in mobile navigation works correctly.
    """
    print("Testing mobile navigation panel...")
    page.set_viewport_size({"width": 375, "height": 667})
    page.goto(BASE_URL)

    hamburger_button = page.get_by_role("button", name="Open menu")
    expect(hamburger_button).to_be_visible()

    print("Clicking hamburger menu...")
    hamburger_button.click()

    nav_panel = page.locator(".nav-links")
    # The panel slides in, so we check for the 'is-active' class
    expect(nav_panel).to_have_class(re.compile(r"is-active"))
    # Wait for the animation to finish
    page.wait_for_timeout(500)

    page.screenshot(path="jules-scratch/verification/03_mobile_nav_panel_open.png")
    print("Mobile navigation panel screenshot captured.")

def test_dashboard_zero_data_state(page: Page):
    """
    Verify that a new user sees the correct "zero-data" states on the dashboard.
    """
    print("Testing dashboard zero-data state...")
    # Create a new unique user to ensure no data exists
    unique_username = f"testuser_{page.context.browser.new_context().storage_state()['origins'][0]['origin'][-8:]}"

    print(f"Signing up as new user: {unique_username}")
    page.goto(f"{BASE_URL}/signup")
    page.get_by_label("Username").fill(unique_username)
    page.get_by_label("Password").fill("password123")
    page.get_by_label("Confirm Password").fill("password123")
    page.get_by_role("button", name="Create My Account").click()

    # Log in as the new user
    print("Logging in...")
    expect(page.get_by_role("heading", name="Sign In")).to_be_visible()
    page.get_by_label("Username").fill(unique_username)
    page.get_by_label("Password").fill("password123")
    page.get_by_role("button", name="Sign In").click()

    # Verify we are on the dashboard
    print("Verifying dashboard content...")
    expect(page.get_by_role("heading", name=f"Welcome, {unique_username}")).to_be_visible()

    # Check for empty states
    expect(page.get_by_text("No Spending Data Yet")).to_be_visible()
    expect(page.get_by_text("No Insights to Show")).to_be_visible()
    print("Verified empty states are visible.")

    page.screenshot(path="jules-scratch/verification/04_dashboard_zero_data_state.png")
    print("Dashboard zero-data state screenshot captured.")

    # Logout
    page.get_by_role("link", name="Logout").click()

def test_admin_panel_styling(page: Page):
    """
    Verify the styling of the main admin dashboard.
    """
    print("Testing admin panel styling...")
    page.goto(f"{BASE_URL}/login")
    page.get_by_label("Username").fill("admin")
    page.get_by_label("Password").fill("admin123")
    page.get_by_role("button", name="Sign In").click()

    print("Navigating to admin dashboard...")
    page.goto(f"{BASE_URL}/admin")

    expect(page.get_by_role("heading", name="Admin Dashboard")).to_be_visible()

    page.screenshot(path="jules-scratch/verification/05_admin_dashboard_styled.png")
    print("Admin dashboard screenshot captured.")

def test_admin_chat_page_styling(page: Page):
    """
    Verify the styling of the admin chat interface.
    """
    print("Testing admin chat page styling...")
    # Assumes admin is already logged in from the previous test function
    page.goto(f"{BASE_URL}/admin/chat")

    expect(page.get_by_role("heading", name="Support Chat Dashboard")).to_be_visible()

    page.screenshot(path="jules-scratch/verification/06_admin_chat_page_styled.png")
    print("Admin chat page screenshot captured.")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            test_homepage_content_and_responsiveness(page)
            test_mobile_navigation_panel(page)
            test_dashboard_zero_data_state(page)
            test_admin_panel_styling(page)
            test_admin_chat_page_styling(page)
        except Exception as e:
            print(f"An error occurred during verification: {e}")
        finally:
            browser.close()
            print("Verification script finished.")

if __name__ == "__main__":
    main()
