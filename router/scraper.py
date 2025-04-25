import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from .parser import parse_device_info

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

    def get_iframe_html(self, iframe_path: str) -> str:
        self.driver.get(f"{self.base_url}/{iframe_path}")
        time.sleep(2)
        return self.driver.page_source

    def scrape_all(self):
        html = self.get_iframe_html("html/ssmp/deviceinfo/deviceinfo.asp")
        data = parse_device_info(html)
        for entry in data:
            print(entry)

    def quit(self):
        self.driver.quit()
