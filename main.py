from router.scraper import RouterScraper
from config import ROUTER_URL, USERNAME, PASSWORD

if __name__ == "__main__":
    scraper = RouterScraper(ROUTER_URL)
    scraper.login(USERNAME, PASSWORD)
    print("\n--- Scraping Device Info ---")
    devices = scraper.scrape_all()

    print("\n--- Scraping Neighbor APs ---")
    neighbors = scraper.scrape_neighboring_aps()
    for ap in neighbors:
        print(ap)
    scraper.quit()

