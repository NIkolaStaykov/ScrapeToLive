import random
import json
from time import sleep
from datetime import datetime as time
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from playsound import playsound

import undetected_chromedriver as uc

# --- Modular Anti-bot and Humanization Utilities ---

def beep(times=1):
    for _ in range(times):
        playsound('audio/notification_sound.mp3')

def human_like_mouse_move(driver, element):
    """Scroll to element in a human-like way and move mouse using Actions."""
    driver.execute_script("""
        var rect = arguments[0].getBoundingClientRect();
        window.scrollBy({top: rect.top - 100, left: 0, behavior: 'smooth'});
    """, element)
    try:
        actions = ActionChains(driver)
        actions.move_to_element(element).perform()
    except Exception:
        pass
    random_sleep(0.4, 1.2)

def random_sleep(a=0.2, b=0.7):
    sleep(random.uniform(a, b))

def spoof_navigator(driver):
    """Spoof navigator properties to appear more human."""
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
                window.chrome = { runtime: {} };
            """
        }
    )

def setup_undetected_chrome_driver(driver_options=None, args=None):
    """Return undetected Chrome driver with anti-bot settings."""
    options = uc.ChromeOptions()
    # options.add_argument("--disable-blink-features=AutomationControlled")
    # options.add_argument("--disable-infobars")
    # options.add_argument("--disable-extensions")
    # options.add_argument("--disable-gpu")
    # options.add_argument("--no-sandbox")
    # options.add_argument("--disable-dev-shm-usage")
    # options.add_argument("--lang=en-US")
    # options.add_argument("--start-maximized")
    # options.add_argument("--disable-features=IsolateOrigins,site-per-process")
    driver_options = driver_options or {}
    args = args or []
    for (k, v) in driver_options.items():
        options.add_experimental_option(k, v)
    for arg in args:
        options.add_argument(arg)
    BROWSER_EXECUTABLE_PATH = "D:\Program_files\chrome-win64\chrome.exe"
    driver = uc.Chrome(options=options, use_subprocess=True, browser_executable_path=BROWSER_EXECUTABLE_PATH)
    spoof_navigator(driver)
    return driver

def cleanup_driver(driver):
    """Ensure driver is closed properly."""
    try:
        driver.quit()
    except Exception:
        pass

# --- Scraper Classes ---

class ScraperBase:
    TIMEOUT = 10
    # PROXIES = [
    #     "https://189.240.60.168:9090",
    #     "https://189.240.60.169:9090",
    #     "https://189.240.60.171:9090",
    #     "https://219.145.250.129:7890",
    #     "https://45.12.150.82:8080",
    #     "https://45.140.143.77:18080",
    #     "https://88.198.212.91:3128",
    #     "https://89.43.31.134:3128"
    # ]

    def __init__(self, driver_options=None, args=None):
        self.driver = None
        self.new_offers = None
        self.seen_offers = set()
        # self.proxy = random.choice(self.PROXIES)
        self.setup_chrome_driver(driver_options, args)

    def setup_chrome_driver(self, driver_options=None, args=None):
        # print(f"Using proxy: {self.proxy}")
        self.driver = setup_undetected_chrome_driver(driver_options, args)

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
        try:
            WebDriverWait(self.driver, self.TIMEOUT).until(
                EC.element_to_be_clickable((By.XPATH, '//button[p[contains(., "Manage options")]]')))
            btn = self.driver.find_element(By.XPATH, '//button[p[contains(., "Manage options")]]')
            human_like_mouse_move(self.driver, btn)
            btn.click()
            random_sleep()

            WebDriverWait(self.driver, self.TIMEOUT).until(
                EC.element_to_be_clickable((By.XPATH, '//button[p[contains(., "Confirm choices")]]')))
            btn2 = self.driver.find_element(By.XPATH, '//button[p[contains(., "Confirm choices")]]')
            human_like_mouse_move(self.driver, btn2)
            btn2.click()
            random_sleep()
        except Exception as e:
            print(f"Cookie handling failed: {e}")

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
        price_max_elem = self.driver.find_element(By.XPATH, '//select[@name="priceMax"]')
        human_like_mouse_move(self.driver, price_max_elem)
        price_max_elem.send_keys(f'{self.search_parameters["price_max"]}')
        random_sleep()

        price_min_elem = self.driver.find_element(By.XPATH, '//select[@name="priceMin"]')
        human_like_mouse_move(self.driver, price_min_elem)
        price_min_elem.send_keys(f'{self.search_parameters["price_min"]}')
        random_sleep()

        wgstate_elem = self.driver.find_element(By.XPATH, '//select[@name="wgState"]')
        human_like_mouse_move(self.driver, wgstate_elem)
        wgstate_elem.send_keys('Zürich (Stadt)')
        random_sleep()

        search_btn = self.driver.find_element(By.XPATH, '//input[@value="Suchen"]')
        human_like_mouse_move(self.driver, search_btn)
        search_btn.click()
        random_sleep()

    def get_new_offers(self):
        try:
            WebDriverWait(self.driver, self.TIMEOUT).until(EC.presence_of_element_located(
                (By.CLASS_NAME, "search-mate-entry")))
        except TimeoutException:
            return False
        unfiltered_offers = self.driver.find_elements(By.XPATH,
                                                     '//li[contains(@class, "search-mate-entry")]')

        self.new_offers = []
        for offer in unfiltered_offers:
            date = offer.find_element(By.XPATH, './/div[contains(@class, "create-date")]').text
            if not date == time.now().strftime('%#d.%#m.%Y'):
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
        self.seen_offers.add(hash(offer.text))

    def handle_offers(self):
        for offer in self.new_offers:
            self.handle_offer(offer)

    def run(self):
        try:
            self.enter_search_parameters()
            print("Starting to crawl...")

            # Initial listing of offers
            status = self.get_new_offers()
            for offer in self.new_offers:
                self.seen_offers.add(hash(offer.text))

            print(f"Initial offers: {len(self.new_offers)}")

            # Main loop checking for new offers
            while True:
                try:
                    sleep(random.randint(75, 180))
                    print(f"Refreshing at {time.now().strftime('%H:%M:%S')}")
                    self.driver.get(self.HOME_URL)
                    # self.enter_search_parameters()
                    status = self.get_new_offers()
                    if not status:
                        print("Something is actively crashing")
                        continue
                    self.handle_offers()
                except Exception as e:
                    print(f"An error occurred: {e}")
        finally:
            cleanup_driver(self.driver)

# --- Main Entrypoint ---

if __name__ == "__main__":
    search_parameters_path = "search_parameters.json"
    search_parameters = json.load(open(search_parameters_path))
    # Parse the min and max search price to string of the form 1.100, they are in the form 1100
    if len(search_parameters['price_min']) >= 4:
        search_parameters['price_min'] = f"{search_parameters['price_min'][:-3]}.{search_parameters['price_min'][-3:]}"
    if len(search_parameters['price_max']) >= 4:
        search_parameters['price_max'] = f"{search_parameters['price_max'][:-3]}.{search_parameters['price_max'][-3:]}"

    driver_options = {"prefs": {"credentials_enable_service": False,
                                "profile.password_manager_enabled": False}
                      }

    args = ["--start-fullscreen", "--log-level=3"]
    # args.append("--headless")

    scraper = WGZimmerScraper(search_parameters, driver_options, args)
    scraper.run()