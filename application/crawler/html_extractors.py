"""
HTML content extraction module.

This module provides the Extractor class for parsing HTML and extracting
structured data including links, images, emails, and cryptocurrency addresses.
"""

import logging
import re
from typing import Dict, List, Optional
from urllib.parse import urlparse, urlunparse

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class Extractor:
    """
    HTML content extractor for web crawling.

    Parses HTML content and extracts structured data including links, images,
    text content, emails, and cryptocurrency addresses.
    """

    def __init__(self, base_url: str, html: str) -> None:
        """
        Initialize the HTML extractor.

        Args:
            base_url: Base URL of the page (used for resolving relative URLs)
            html: Raw HTML content to parse
        """
        self.html = html
        self.soup = BeautifulSoup(html, "lxml")
        self.base_url = base_url

    def get_links(self) -> List[Dict[str, any]]:
        """
        Extract all links from the HTML.

        Parses all anchor tags and extracts URLs, resolving relative URLs
        to absolute URLs. Determines if each link is an onion address and
        whether it's in scope (same domain as base URL).
        
        Note: This method identifies .onion addresses but does not validate
        the address format. Validation for Onion v3 format (56-character
        addresses) occurs downstream via is_valid_onion_url().

        Returns:
            List of dictionaries with keys:
                - url: The link URL (absolute)
                - is_onion: Whether the URL is an onion address
                - in_scope: Whether the URL is on the same domain
        """
        parsed_url = urlparse(self.base_url)
        _urls = []
        for link in self.soup.find_all("a"):
            href = link.get("href")
            parsed_href = urlparse(href)
            in_scope = False
            # Check if URL is an onion address (v3 format validation happens downstream)
            is_onion = True if ".onion" in parsed_href.netloc else False

            if parsed_href.netloc != "":
                href = urlunparse((parsed_href.scheme, parsed_href.netloc, parsed_href.path, "", parsed_href.query, ""))
            if parsed_href.netloc != "":
                if parsed_href.netloc == parsed_url.netloc:
                    in_scope = True
                    href = urlunparse(
                        (parsed_url.scheme, parsed_url.netloc, parsed_href.path, "", parsed_href.query, "")
                    )
            if href.startswith("/") or href.startswith("?"):
                in_scope = True
                href = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_href.path, "", parsed_href.query, ""))
            if href.startswith("#"):
                in_scope = True
                href = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_href.path, "", parsed_href.query, ""))
            _urls.append({"url": href, "is_onion": is_onion, "in_scope": in_scope})
        return _urls

    def get_body(self) -> Optional[str]:
        """
        Extract body text from HTML.

        Returns:
            Body text with whitespace normalized, or None if extraction fails
        """
        try:
            return self.soup.body.get_text(" ", strip=True)
        except AttributeError as e:
            logger.warning(f"No body tag found in HTML: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error extracting body text: {str(e)}")
            return None

    def get_title(self) -> Optional[str]:
        """
        Extract page title from HTML.

        Returns:
            Page title text, or None if no title tag exists
        """
        try:
            return self.soup.title.get_text()
        except AttributeError:
            logger.debug("No title tag found in HTML")
            return None
        except Exception as e:
            logger.error(f"Error extracting title: {str(e)}")
            return None

    def get_img_links(self) -> List[str]:
        """
        Extract all image URLs from the HTML.

        Parses all img tags and extracts src attributes, resolving relative
        URLs to absolute URLs.

        Returns:
            List of image URLs (absolute)
        """
        parsed_url = urlparse(self.base_url)
        _imgs = []
        for link in self.soup.find_all("img"):
            src = link.get("src")
            parsed_src = urlparse(src)

            if parsed_src.netloc != "":
                src = urlunparse((parsed_src.scheme, parsed_src.netloc, parsed_src.path, "", parsed_src.query, ""))
            if parsed_src.netloc != "":
                if parsed_src.netloc == parsed_url.netloc:
                    src = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_src.path, "", parsed_src.query, ""))
            if src.startswith("/") or src.startswith("?"):
                src = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_src.path, "", parsed_src.query, ""))
            _imgs.append(src)
        return _imgs

    def get_emails(self) -> Optional[List[str]]:
        """
        Extract email addresses from HTML.

        Uses regex pattern matching to find email addresses in the HTML content.

        Returns:
            List of email addresses found, or None if extraction fails
        """
        try:
            match = re.findall(r"[\w\.-]+@[\w\.-]+", self.html)
            return match
        except Exception as e:
            logger.error(f"Error extracting emails: {str(e)}")
            return None

    def get_pgps(self) -> Optional[List[str]]:
        """
        Extract PGP public keys from HTML.

        Uses regex pattern matching to find PGP public key blocks in the HTML.

        Returns:
            List of PGP public key blocks found, or None if extraction fails
        """
        try:
            match = re.findall(
                r"-----BEGIN PGP PUBLIC KEY BLOCK-----((?s).*)-----END PGP PUBLIC KEY BLOCK-----", self.html
            )
            return match
        except Exception as e:
            logger.error(f"Error extracting PGP keys: {str(e)}")
            return None

    def get_bitcoin_addrs(self) -> Optional[List[str]]:
        """
        Extract Bitcoin addresses from body text.

        Uses regex pattern matching to find Bitcoin addresses in the page body.
        Matches addresses starting with 1 or 3 (legacy format).

        Returns:
            List of Bitcoin addresses found, or None if extraction fails
        """
        try:
            body_text = self.get_body()
            if body_text:
                _find = re.findall("[13][a-km-zA-HJ-NP-Z1-9]{25,34}", body_text)
                return _find
            return None
        except Exception as e:
            logger.error(f"Error extracting Bitcoin addresses: {str(e)}")
            return None

    def get_eth_addrs(self) -> Optional[List[str]]:
        """
        Extract Ethereum addresses from body text.

        Uses regex pattern matching to find Ethereum addresses in the page body.
        Matches addresses starting with 0x followed by 40 hex characters.

        Returns:
            List of Ethereum addresses found, or None if extraction fails
        """
        try:
            body_text = self.get_body()
            if body_text:
                _find = re.findall("0x[a-fA-F0-9]{40}", body_text)
                return _find
            return None
        except Exception as e:
            logger.error(f"Error extracting Ethereum addresses: {str(e)}")
            return None

    def get_monero_addrs(self) -> Optional[List[str]]:
        """
        Extract Monero addresses from body text.

        Uses regex pattern matching to find Monero addresses in the page body.
        Matches addresses starting with 4 followed by specific character patterns.

        Returns:
            List of Monero addresses found, or None if extraction fails
        """
        try:
            body_text = self.get_body()
            if body_text:
                _find = re.findall("4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}", body_text)
                return _find
            return None
        except Exception as e:
            logger.error(f"Error extracting Monero addresses: {str(e)}")
            return None
