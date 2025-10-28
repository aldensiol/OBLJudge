import dateutil.parser
import requests

from bs4 import BeautifulSoup
from typing import Optional, Dict, Any
from newspaper import Article

from src.utils import setup_logger


class ArticleCrawler:
    def __init__(self):
        self.logger = setup_logger(f"[{self.__class__.__name__}]")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

    def _extract_publish_date(self, soup: BeautifulSoup) -> Optional[str]:
        """
        extracts the publish date from multiple sources
        """
        # meta tags to check for publish date
        meta_tags = [
            ("property", "article:published_time"),
            ("property", "og:published_time"),
            ("name", "publishdate"),
            ("name", "publish_date"),
            ("name", "date"),
            ("property", "og:article:published_time"),
            ("name", "article.published"),
            ("itemprop", "datePublished"),
            ("name", "publication_date"),
        ]

        for attr, value in meta_tags:
            meta = soup.find("meta", attrs={attr: value})
            if meta and meta.get("content"):
                try:
                    parsed_date = dateutil.parser.parse(meta.get("content"))
                    return parsed_date.isoformat()
                except:
                    continue

        # look for time tags with datetime attribute
        time_tags = soup.find_all("time")
        for time_tag in time_tags:
            datetime_attr = time_tag.get("datetime")
            if datetime_attr:
                try:
                    parsed_date = dateutil.parser.parse(datetime_attr)
                    return parsed_date.isoformat()
                except:
                    continue

        # look for json-ld structured data
        json_ld_date = self._extract_from_json_ld(soup, "datePublished")
        if json_ld_date:
            return json_ld_date

        return None

    def _extract_update_date(self, soup: BeautifulSoup) -> Optional[str]:
        """
        extracts the update date from meta tags
        """
        # common meta tags for update dates
        meta_tags = [
            ("property", "article:modified_time"),
            ("name", "last-modified"),
            ("property", "og:updated_time"),
            ("name", "updated_time"),
            ("property", "og:article:modified_time"),
            ("name", "article.updated"),
            ("itemprop", "dateModified"),
            ("name", "lastmod"),
        ]

        for attr, value in meta_tags:
            meta = soup.find("meta", attrs={attr: value})
            if meta and meta.get("content"):
                try:
                    parsed_date = dateutil.parser.parse(meta.get("content"))
                    return parsed_date.isoformat()
                except:
                    continue

        # look for json-ld structured data
        json_ld_date = self._extract_from_json_ld(soup, "dateModified")
        if json_ld_date:
            return json_ld_date

        return None

    def _extract_from_json_ld(
        self, soup: BeautifulSoup, date_field: str
    ) -> Optional[str]:
        """
        extracts date from json-ld structured data
        """
        import json

        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            try:
                data = json.loads(script.string)

                # handle both single objects and arrays
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and date_field in item:
                            parsed_date = dateutil.parser.parse(item[date_field])
                            return parsed_date.isoformat()
                elif isinstance(data, dict) and date_field in data:
                    parsed_date = dateutil.parser.parse(data[date_field])
                    return parsed_date.isoformat()
            except:
                continue

        return None

    def scrape_article(self, url: str) -> Dict[str, Any]:
        """
        scrapes article content from a given url
        """
        try:
            self.logger.info(f"scraping article from: {url}")

            # use newspaper3k for article extraction
            article = Article(url)
            article.download()
            article.parse()

            # extract metadata
            content = article.text

            # get the html for date extraction
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")

            # try multiple methods to extract dates
            publish_date = (
                article.publish_date.isoformat()
                if article.publish_date
                else self._extract_publish_date(soup)
            )

            update_date = self._extract_update_date(soup)

            result = {
                "url": url,
                "publish_date": publish_date,
                "update_date": update_date,
                "content": content,
                "title": article.title,
                "authors": article.authors,
            }

            self.logger.info(
                f"extracted - title: {article.title}, publish: {publish_date}, update: {update_date}"
            )
            return result

        except Exception as e:
            self.logger.error(f"failed to scrape article from {url}: {str(e)}")
            return {
                "url": url,
                "publish_date": None,
                "update_date": None,
                "content": None,
                "title": None,
                "authors": [],
            }
