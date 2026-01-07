from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, ElementTree
import io

PORT = 10000
SOURCE = "https://www.moneymetals.com/news"

HEADERS = {"User-Agent": "Mozilla/5.0"}

def build_rss():
    html = requests.get(SOURCE, headers=HEADERS, timeout=20).text
    soup = BeautifulSoup(html, "html.parser")

    rss = Element("rss", version="2.0")
    channel = SubElement(rss, "channel")

    SubElement(channel, "title").text = "MoneyMetals News"
    SubElement(channel, "link").text = SOURCE
    SubElement(channel, "description").text = "MoneyMetals News RSS"
    SubElement(channel, "lastBuildDate").text = datetime.utcnow().strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )

    seen = set()

    for a in soup.select("a[href^='/news/']"):
        title = a.get_text(strip=True)
        if not title:
            continue

        link = "https://www.moneymetals.com" + a["href"]
        if link in seen:
            continue
        seen.add(link)

        item = SubElement(channel, "item")
        SubElement(item, "title").text = title
        SubElement(item, "link").text = link
        SubElement(item, "guid").text = link
        SubElement(item, "pubDate").text = datetime.utcnow().strftime(
            "%a, %d %b %Y %H:%M:%S GMT"
        )

    buf = io.BytesIO()
    ElementTree(rss).write(buf, encoding="utf-8", xml_declaration=True)
    return buf.getvalue()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/moneymetals.xml":
            self.send_response(404)
            self.end_headers()
            return

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


HTTPServer(("", PORT), Handler).serve_forever()
