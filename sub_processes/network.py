from seleniumwire import webdriver  # selenium-wire
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time
import threading
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class _123AVWebManager:
    def __init__(self):
        self.driver = self.setup()

    def setup(self):
        options = Options()
        # options.add_argument('--headless=new')
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        return driver

    def monitor_requests(self, driver, keyword, stop_flag, result_holder, timeout):
        seen = set()
        start_time = time.time()
        while not stop_flag[0]:
            for req in driver.requests:
                if req.url not in seen:
                    seen.add(req.url)
                    if keyword in req.url:
                        print(">>> MATCH:", req.url)
                        result_holder[0] = req.url  # URLを保持
                        stop_flag[0] = True
                        break
            if time.time() - start_time > timeout:
                print(">>> TIMEOUT")
                stop_flag[0] = True
                break
            time.sleep(0.3)

    def get_master_url(self, url, timeout=20):
        stop_flag = [False]
        result_holder = [None]

        monitor_thread = threading.Thread(
            target=self.monitor_requests,
            args=(self.driver, "video.m3u8?v=a2", stop_flag, result_holder, timeout)
        )
        monitor_thread.start()

        try:
            self.driver.get(url)
            while not stop_flag[0]:
                time.sleep(0.5)
        finally:
            self.driver.quit()
            monitor_thread.join()

        return result_holder[0]  # ← URLを返す
    

    def click(self, index):
        wait = WebDriverWait(self.driver, 10)
        element = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f'#scenes [data-index="{index}"]'))
        )
        element.click()