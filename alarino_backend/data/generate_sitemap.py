#!/usr/bin/env python3
# generate_sitemap.py
import os
from datetime import datetime
from typing import List, Optional, Set
import xml.dom.minidom
from xml.etree import ElementTree
from urllib.parse import quote

# Add the parent directory to the path to import the app modules
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import the app modules
from main import app, logger
from main.db_models import Word, Translation
from main.languages import Language

# Add this to your crontab with: crontab -e
# Run the sitemap generator every day at 1:00 AM
# 0 1 * * * cd alarino_backend/data && /usr/bin/python3 data/generate_sitemap.py >> data/sitemap_generation.log 2>&1

SITE_DOMAIN = os.getenv("SITE_DOMAIN", "https://alarino.com")  # Default domain, override with environment variable

def generate_sitemap(output_path: str) -> None:
    """
    Generate a sitemap.xml file for Alarino containing all english words in the database.
    Args:
        output_path: Path where the sitemap.xml file will be saved
    """
    logger.info("Starting sitemap generation...")

    # Create the root element
    urlset = ElementTree.Element(
        "urlset",
        {"xmlns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    )

    # Add the homepage
    add_url(urlset, f"{SITE_DOMAIN}/", "1.0", "daily")

    # Set to track words we've already added to avoid duplicates
    processed_words: Set[str] = set()

    # Get all English words that have translations to Yoruba
    english_words: List[Word] = (
        Word.query
        .filter_by(language=Language.ENGLISH)
        .join(Translation, Word.w_id == Translation.source_word_id)
        .all()
    )

    logger.info(f"Found {len(english_words)} English words with translations")

    # Add English word pages
    for word in english_words:
        word_text = word.word.strip().lower()
        if word_text and word_text not in processed_words:
            processed_words.add(word_text)
            # Create word-specific URL with proper encoding
            word_url = f"{SITE_DOMAIN}/word/{quote(word_text)}"
            add_url(urlset, word_url, "0.8", "weekly")

    # Create the XML tree and prettify it
    tree = ElementTree.ElementTree(urlset)
    xml_string = ElementTree.tostring(urlset, encoding="utf-8")

    # Use minidom to prettify the XML
    pretty_xml = xml.dom.minidom.parseString(xml_string).toprettyxml(indent="  ")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(pretty_xml)

    logger.info(f"Sitemap generated at {output_path} with {len(processed_words) + 1} URLs")


def add_url(
        urlset: ElementTree.Element,
        loc: str,
        priority: str,
        changefreq: str,
        lastmod: Optional[str] = None
) -> None:
    """
    Add a URL to the sitemap.

    Args:
        urlset: The parent urlset element
        loc: URL location
        priority: Priority value (0.0 to 1.0)
        changefreq: Change frequency (always, hourly, daily, weekly, monthly, yearly, never)
        lastmod: Last modification date (optional, defaults to today)
    """
    url = ElementTree.SubElement(urlset, "url")
    ElementTree.SubElement(url, "loc").text = loc

    # Use current date if lastmod is not provided
    if lastmod is None:
        lastmod = datetime.now().strftime("%Y-%m-%d")

    # ElementTree.SubElement(url, "lastmod").text = lastmod
    ElementTree.SubElement(url, "changefreq").text = changefreq
    ElementTree.SubElement(url, "priority").text = priority


if __name__ == "__main__":
    # Use app context to access database
    with app.app_context():
        output_file = "sitemap.xml"
        generate_sitemap(output_file)