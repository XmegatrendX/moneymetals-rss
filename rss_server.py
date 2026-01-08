import requests
from bs4 import BeautifulSoup
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime
import xml.etree.ElementTree as ET
import email.utils
import os

SOURCE_URL = "https://www.moneymetals.com/news"
BASE_URL = "https://www.moneymetals.com"


def build_rss():
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; RSSBot/1.0)"
    }

    r = requests.get(SOURCE_URL, headers=headers, timeout=20)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = "Money Metals News"
    ET.SubElement(channel, "link").text = SOURCE_URL
    ET.SubElement(channel, "description").text = "Latest news from MoneyMetals.com"
    ET.SubElement(channel, "lastBuildDate").text = email.utils.formatdate(usegmt=True)

    # === ПАРСИНГ ===
    for block in soup.select("div.flex.mb-8.px-4"):
        a = block.select_one("a[href]")
        date_p = block.select_one("p.text-slate-500")

        if not a or not date_p:
            continue

        title = a.get_text(strip=True)
        link = a["href"]
        if link.startswith("/"):
            link = BASE_URL + link

        date_text = date_p.get_text(strip=True)

        try:
            pub_date = datetime.strptime(date_text, "%B %dth, %Y")
        except Exception:
            try:
                pub_date = datetime.strptime(date_text, "%B %dst, %Y")
            except Exception:
                try:
                    pub_date = datetime.strptime(date_text, "%B %dnd, %Y")
                except Exception:
                    try:
                        pub_date = datetime.strptime(date_text, "%B %drd, %Y")
                    except Exception:
                        pub_date = datetime.utcnow()

        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = title
        ET.SubElement(item, "link").text = link
        ET.SubElement(item, "guid").text = link
        ET.SubElement(item, "pubDate").text = email.utils.format_datetime(pub_date)

    return ET.tostring(rss, encoding="utf-8", xml_declaration=True)


class Handler(BaseHTTPRequestHandler):

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if self.path in ("/", "/moneymetals.xml"):
            try:
                rss = build_rss()
                self.send_response(200)
                self.send_header("Content-Type", "application/rss+xml; charset=utf-8")
                self.end_headers()
                self.wfile.write(rss)
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())
        elif self.path == "/check":
            self.send_response(200)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
