import xml.etree.ElementTree as ET


def generate_sitemap(pages, base_url):
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

    for page, lastmod, changefreq, priority in pages:
        url = ET.SubElement(urlset, "url")
        loc = ET.SubElement(url, "loc")
        loc.text = f"{base_url.rstrip('/')}/{page.lstrip('/')}"

        if lastmod:
            lastmod_elem = ET.SubElement(url, "lastmod")
            lastmod_elem.text = lastmod

        if changefreq:
            changefreq_elem = ET.SubElement(url, "changefreq")
            changefreq_elem.text = changefreq

        if priority:
            priority_elem = ET.SubElement(url, "priority")
            priority_elem.text = str(priority)

    return ET.tostring(urlset, encoding='utf-8', method='xml').decode()


def main():
    base_url = input("Enter the base URL (e.g., https://example.com): ")
    print(
        "Enter the pages (format: path lastmod changefreq priority, one per line, leave empty to finish):")
    pages = []
    while True:
        entry = input().strip()
        if not entry:
            break
        parts = entry.split()
        page = parts[0]
        lastmod = parts[1] if len(parts) > 1 else ""
        changefreq = parts[2] if len(parts) > 2 else ""
        priority = parts[3] if len(parts) > 3 else ""
        pages.append((page, lastmod, changefreq, priority))

    sitemap = generate_sitemap(pages, base_url)

    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(sitemap)

    print("Sitemap generated and saved as sitemap.xml")


