import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

NETWORK_LOG = LOG_DIR / "network_log.txt"
CONSOLE_LOG = LOG_DIR / "console_log.txt"


def append_line(path: Path, text: str) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(text + "\n")


def safe_json(data):
    try:
        return json.dumps(data, indent=2)
    except Exception:
        return str(data)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)
        context = browser.new_context()
        page = context.new_page()

        # Clear old logs
        NETWORK_LOG.write_text("", encoding="utf-8")
        CONSOLE_LOG.write_text("", encoding="utf-8")

        # --- Network hooks ---
        def on_request(request):
            msg = [
                "=" * 80,
                f"[REQUEST] {request.method} {request.url}",
                f"Resource type: {request.resource_type}",
            ]
            if request.post_data:
                msg.append("POST DATA:")
                msg.append(request.post_data)
            append_line(NETWORK_LOG, "\n".join(msg))

        def on_response(response):
            msg = [
                "-" * 80,
                f"[RESPONSE] {response.status} {response.url}",
            ]
            try:
                content_type = response.headers.get("content-type", "")
                msg.append(f"Content-Type: {content_type}")

                # Only try to capture readable payloads
                if (
                    "application/json" in content_type
                    or "text/" in content_type
                    or "javascript" in content_type
                ):
                    body = response.text()
                    if len(body) > 3000:
                        body = body[:3000] + "\n...[truncated]..."
                    msg.append(body)
            except Exception as e:
                msg.append(f"[Could not read response body: {e}]")

            append_line(NETWORK_LOG, "\n".join(msg))

        page.on("request", on_request)
        page.on("response", on_response)

        # --- Console hooks ---
        def on_console(msg):
            append_line(CONSOLE_LOG, f"[{msg.type.upper()}] {msg.text}")

        def on_page_error(err):
            append_line(CONSOLE_LOG, f"[PAGEERROR] {err}")

        page.on("console", on_console)
        page.on("pageerror", on_page_error)

        # --- Go to simulator ---
        url = "https://dalton-nrs.manchester.ac.uk/"
        page.goto(url, wait_until="networkidle")

        print("\nOpened simulator.")
        print("Now do this manually in the browser:")
        print("1. Start the simulator")
        print("2. Turn pumps on")
        print("3. Move control rods")
        print("4. Change steam output")
        print("5. Play for 1-2 minutes")
        print("\nLogs will be written to:")
        print(f"  {NETWORK_LOG.resolve()}")
        print(f"  {CONSOLE_LOG.resolve()}")
        print("\nPress ENTER here when you're done...")

        input()

        # Save page HTML too
        html_path = LOG_DIR / "page_snapshot.html"
        html_path.write_text(page.content(), encoding="utf-8")

        print(f"Saved page HTML to: {html_path.resolve()}")

        browser.close()


if __name__ == "__main__":
    main()