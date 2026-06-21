import json
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright, BrowserContext

SESSIONS_DIR = Path(__file__).parent.parent / "sessions"
SESSIONS_DIR.mkdir(exist_ok=True)


def session_path(site: str) -> Path:
    return SESSIONS_DIR / f"{site}.json"


def has_session(site: str) -> bool:
    return session_path(site).exists()


async def open_login_browser(site: str, login_url: str) -> None:
    """Open a visible browser for the user to log in, then save session."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        ctx = await browser.new_context()
        page = await ctx.new_page()
        await page.goto(login_url)
        print(f"\n>>> Log in to {site} in the browser window that just opened.")
        print(">>> When you are fully logged in, come back here and press ENTER.")
        input()
        storage = await ctx.storage_state()
        session_path(site).write_text(json.dumps(storage))
        await browser.close()
        print(f">>> Session saved for {site}.")


async def get_authenticated_context(site: str, playwright) -> BrowserContext | None:
    """Return a browser context loaded with saved session cookies."""
    sp = session_path(site)
    if not sp.exists():
        return None
    storage = json.loads(sp.read_text())
    browser = await playwright.chromium.launch(headless=True)
    ctx = await browser.new_context(storage_state=storage)
    return ctx


def run_login(site: str, login_url: str) -> None:
    asyncio.run(open_login_browser(site, login_url))
