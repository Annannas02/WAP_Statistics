from router.scraper import RouterScraper
from config import ROUTER_URL, USERNAME, PASSWORD

if __name__ == "__main__":
    scraper = RouterScraper(ROUTER_URL)
    scraper.login(USERNAME, PASSWORD)
    scraper.scrape_all()
    scraper.quit()

