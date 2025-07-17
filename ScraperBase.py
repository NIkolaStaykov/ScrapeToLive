import random
from seleniumwire import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from time import sleep
from datetime import datetime as time
import json

from playsound import playsound


def beep(times=1):
    for i in range(times):
        playsound('audio/notification_sound.mp3')


class ScraperBase:
    TIMEOUT = 10
    PROXIES = ["https://189.240.60.168:9090",
                "https://189.240.60.169:9090",
                "https://189.240.60.171:9090",
                "https://219.145.250.129:7890",
                "https://45.12.150.82:8080",
                "https://45.140.143.77:18080",
                "https://88.198.212.91:3128",
                "https://89.43.31.134:3128"]

    def __init__(self, driver_options=None, args=None):
        self.driver = None
        self.new_offers = None
        self.seen_offers = []
        self.driver = None
        self.proxy = random.choice(self.PROXIES)
        self.setup_chrome_driver(driver_options, args)

    def setup_chrome_driver(self, driver_options=None, args=None):
        args = args or []
        driver_options = driver_options or {}
        print(f"Using proxy: {self.proxy}")
        seleniumwire_options = {
            # "proxy": {
            #     "http": self.proxy,
            #     "https": self.proxy
            # },
        }
        chrome_options = Options()

        for (k, v) in driver_options.items():
            chrome_options.add_experimental_option(k, v)
        for arg in args:
            chrome_options.add_argument(arg)

        # create the initial window
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            seleniumwire_options=seleniumwire_options,
            options=chrome_options
        )

    def login(self):
        raise NotImplementedError

    def handle_offers(self):
        for offer in self.new_offers:
            self.handle_offer(offer)

    def handle_offer(self, offer):
        raise NotImplementedError

    def get_new_offers(self):
        raise NotImplementedError

    def handle_cookies(self):
        WebDriverWait(self.driver, self.TIMEOUT).until(
            EC.element_to_be_clickable((By.XPATH, '//button[p[contains(., "Manage options")]]')))
        self.driver.find_element(By.XPATH, '//button[p[contains(., "Manage options")]]').click()

        WebDriverWait(self.driver, self.TIMEOUT).until(
            EC.element_to_be_clickable((By.XPATH, '//button[p[contains(., "Confirm choices")]]')))
        self.driver.find_element(By.XPATH, '//button[p[contains(., "Confirm choices")]]').click()

    def run(self):
        raise NotImplementedError


class WGZimmerScraper(ScraperBase):
    HOME_URL = "https://www.wgzimmer.ch/wgzimmer/search/mate.html"

    def __init__(self, search_parameters=None, driver_options=None, args=None):
        super().__init__(driver_options, args)
        self.search_parameters = search_parameters

        self.driver.get(self.HOME_URL)
        self.handle_cookies()

    def enter_search_parameters(self):
        self.driver.find_element(By.XPATH, '//select[@name="priceMax"]').send_keys(f'{self.search_parameters["price_max"]}')
        self.driver.find_element(By.XPATH, '//select[@name="priceMin"]').send_keys(f'{self.search_parameters["price_min"]}')
        # self.driver.find_element(By.XPATH, '//select[@name="wgState"]').send_keys('Zürich (Stadt)')
        self.driver.find_element(By.XPATH, '//input[@value="Suchen"]').click()

    def get_new_offers(self):
        try:
            WebDriverWait(self.driver, self.TIMEOUT).until(EC.presence_of_element_located(
                (By.CLASS_NAME, "search-mate-entry")))
        except TimeoutException:
            return False
        unfiltered_offers = self.driver.find_elements(By.XPATH,
                                                     '//li[contains(@class, "search-mate-entry")]')
        zurich_offers = filter(lambda offer:
                                "Zürich" in offer.find_element(By.XPATH, './/span[contains(@class, "thumbState")]').text,
                                unfiltered_offers)
        self.new_offers = []
        for offer in zurich_offers:
            date = offer.find_element(By.XPATH, './/div[contains(@class, "create-date")]').text
            if not date == time.now().strftime('%-d.%-m.%Y'):
                continue
            elif hash(offer.text) not in self.seen_offers:
                self.new_offers.append(offer)

        return True

    def handle_offer(self, offer: WebElement):
        beep()
        print("-" * 50 + "\n")
        print("New offer at {}".format(time.now().strftime("%H:%M:%S")))
        print(offer.text)
        print(offer.find_element(By.XPATH, './/a').get_attribute('href'))
        self.seen_offers.append(hash(offer.text))

    def handle_offers(self):
        for offer in self.new_offers:
            self.handle_offer(offer)

    def run(self):
        self.enter_search_parameters()
        print("Starting to crawl...")

        # Initial listing of offers
        status = self.get_new_offers()
        for offer in self.new_offers:
            self.seen_offers.append(hash(offer.text))

        print(f"Initial offers: {len(self.new_offers)}")

        # Main loop checking for new offers
        while True:
            try:
                # sleep(random.randint(2, 4))
                sleep(random.randint(75, 180))
                print(f"Refreshing at {time.now().strftime('%H:%M:%S')}")
                # THIS TRIGGERS THE RECAPTCHA AND RETURNS US TO THE HOME PAGE
                self.driver.refresh()
                self.enter_search_parameters()
                status = self.get_new_offers()
                if not status:
                    print("Something is actively crashing")
                    continue
                self.handle_offers()
            except Exception as e:
                print(f"An error occurred: {e}")



if __name__ == "__main__":
    search_parameters_path = "search_parameters.json"
    search_parameters = json.load(open(search_parameters_path))
    # Parse the min and max search price to string of the form 1.100, they are in the form 1100
    if len(search_parameters['price_min']) >= 4:
        search_parameters['price_min'] = f"{search_parameters['price_min'][:-3]}.{search_parameters['price_min'][-3:]}"
    if len(search_parameters['price_max']) >= 4:
        search_parameters['price_max'] = f"{search_parameters['price_max'][:-3]}.{search_parameters['price_max'][-3:]}"

    driver_options = {"useAutomationExtension": False,
                      "excludeSwitches": ["enable-automation"],
                      "prefs": {"credentials_enable_service": False,
                                "profile.password_manager_enabled": False}
                      }

    args = ["--start-fullscreen", "window-size=1920x1080", "--log-level=3",
            "user-agent=Mozilla/127.0 (Windows NT 10.0; Win64; x64) Chrome/128.0.6555.0"]
    # args.append("--headless")

    scraper = WGZimmerScraper(search_parameters, driver_options, args)
    scraper.run()
