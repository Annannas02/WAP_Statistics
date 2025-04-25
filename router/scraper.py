import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from .parser import parse_device_list, parse_device_details, extract_total_pages
from .data_models import DeviceInfo
from bs4 import BeautifulSoup

class RouterScraper:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.driver = webdriver.Firefox(service=Service("geckodriver.exe"))

    def login(self, username: str, password: str):
        self.driver.get(self.base_url)
        time.sleep(1)
        self.driver.find_element(By.ID, "txt_Username").send_keys(username)
        self.driver.find_element(By.ID, "txt_Password").send_keys(password)
        self.driver.find_element(By.ID, "button").click()
        time.sleep(2)

    def get_page_html(self, path: str) -> str:
        self.driver.get(f"{self.base_url}/{path}")
        time.sleep(2)
        return self.driver.page_source

    def scrape_all(self):
        initial_html = self.get_page_html("html/bbsp/userdevinfo/userdevinfo.asp?1")
        total_pages = extract_total_pages(initial_html)
        print(f"Found {total_pages} page(s) of devices.")

        all_devices: list[DeviceInfo] = []
        global_index = 0  # << Track the total device index across pages

        for page in range(1, total_pages + 1):
            print(f"Scraping page {page}...")
            page_html = self.get_page_html(f"html/bbsp/userdevinfo/userdevinfo.asp?{page}")
            device_list = parse_device_list(page_html)

            for _ in device_list:
                detail_html = self.get_page_html(f"html/bbsp/userdevinfo/userdetdevinfo.asp?{global_index}?{page}")
                device_info = parse_device_details(detail_html)
                print(device_info)
                all_devices.append(device_info)
                global_index += 1

        return all_devices
    def quit(self):
        self.driver.quit()