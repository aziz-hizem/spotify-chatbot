import json
import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

BASE_URL = "https://developer.spotify.com"

async def scrape():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Step 1: Open the Reference Index Page
        print("Navigating to API reference index...")
        await page.goto(f"{BASE_URL}/documentation/web-api/reference", timeout=60000)
        await asyncio.sleep(2)  # Optional delay
        await page.wait_for_selector("a[href*='/reference/']", state="attached")


        # Step 2: Extract all endpoint links
        content = await page.content()
        soup = BeautifulSoup(content, "html.parser")

        links = soup.select("a[href^='/documentation/web-api/reference/']")
        endpoint_urls = list(set([BASE_URL + link["href"] for link in links if "/reference/" in link["href"]]))

        print(f"Found {len(endpoint_urls)} endpoint pages.")

        data = []

        # Step 3: Visit each endpoint page
        for url in endpoint_urls:
            print(f"Scraping: {url}")
            await page.goto(url, timeout=60000)
            await page.wait_for_selector("h1")

            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")

            # Extract the title
            title = soup.find("h1").get_text(strip=True)

            # Extract endpoint method + path
            endpoint_tag = soup.find("code", class_="block")
            endpoint_line = endpoint_tag.get_text(strip=True) if endpoint_tag else None

            # Split method and path (e.g., "GET /v1/me/player")
            method, path = None, None
            if endpoint_line and " " in endpoint_line:
                method, path = endpoint_line.split(" ", 1)

            # Description
            desc_tag = soup.find("div", class_="prose")
            description = desc_tag.get_text(separator="\n", strip=True) if desc_tag else ""

            # Scopes (if any)
            scopes_section = soup.find("h2", string=lambda t: t and "scope" in t.lower())
            scopes = []
            if scopes_section:
                ul = scopes_section.find_next("ul")
                if ul:
                    scopes = [li.get_text(strip=True) for li in ul.find_all("li")]

            # Parameters
            params = {}
            param_section = soup.find("h2", string=lambda t: t and "parameters" in t.lower())
            if param_section:
                table = param_section.find_next("table")
                if table:
                    for row in table.find_all("tr")[1:]:  # Skip header
                        cols = row.find_all("td")
                        if len(cols) >= 2:
                            param_name = cols[0].get_text(strip=True)
                            param_desc = cols[1].get_text(strip=True)
                            params[param_name] = param_desc

            data.append({
                "title": title,
                "method": method,
                "path": path,
                "url": url,
                "description": description,
                "scopes": scopes,
                "parameters": params
            })

        # Step 4: Save to JSON
        with open("data/endpoints.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        await browser.close()
        print("✅ Done. Data saved to data/endpoints.json")

if __name__ == "__main__":
    asyncio.run(scrape())
