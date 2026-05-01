import requests
import logging
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

logger = logging.getLogger("checker")

class DarkWebScraper:
    """
    Scraper for identifying leaks on the Dark Web and Paste sites.
    """
    
    AHMIA_URL = "https://ahmia.fi/search/?q="
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })

    def search_ahmia(self, query: str):
        """
        Searches the Ahmia onion index (Clear web proxy to the dark web).
        """
        results = []
        try:
            url = f"{self.AHMIA_URL}{quote_plus(query)}"
            logger.info(f"Searching Ahmia for: {query}")
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Ahmia search results are in 'li' elements with class 'result'
                search_results = soup.find_all('li', class_='result')
                
                for res in search_results[:10]: # Limit to top 10
                    title_elem = res.find('a')
                    snippet_elem = res.find('p')
                    
                    if title_elem:
                        url = title_elem.get('href', '')
                        # Clean up Ahmia redirect URLs if necessary
                        if url.startswith("/redirect/"):
                            url = url.split("redirect_url=")[-1]
                        
                        results.append({
                            'source_type': 'dark_web',
                            'title': title_elem.text.strip(),
                            'url': url,
                            'snippet': snippet_elem.text.strip() if snippet_elem else ""
                        })
            else:
                logger.error(f"Ahmia search failed with status: {response.status_code}")
        except Exception as e:
            logger.error(f"Error searching Ahmia: {e}")
            
        return results

    def search_pastebin(self, query: str):
        """
        Searches for keywords on Pastebin via Ahmia or common search proxies.
        """
        results = []
        # Since direct Pastebin scraping is hard, we can leverage Ahmia's ability to index pastes
        # or use a specialized query.
        try:
            search_query = f"site:pastebin.com {query}"
            url = f"{self.AHMIA_URL}{quote_plus(search_query)}"
            logger.info(f"Searching Pastebin leaks via Ahmia for: {query}")
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                search_results = soup.find_all('li', class_='result')
                
                for res in search_results[:5]:
                    title_elem = res.find('a')
                    snippet_elem = res.find('p')
                    
                    if title_elem:
                        results.append({
                            'source_type': 'pastebin',
                            'title': title_elem.text.strip(),
                            'url': title_elem.get('href', ''),
                            'snippet': snippet_elem.text.strip() if snippet_elem else ""
                        })
        except Exception as e:
            logger.error(f"Error searching Pastebin: {e}")
            
        return results

    def run_all_scans(self, query: str):
        """
        Runs both Dark Web and Pastebin scans.
        """
        all_results = []
        all_results.extend(self.search_ahmia(query))
        all_results.extend(self.search_pastebin(query))
        return all_results
