from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import logging
from dotenv import load_dotenv
import os

load_dotenv()

class InstagramNotifier:
    def __init__(self):
        self.username = os.getenv('INSTAGRAM_USER')
        self.password = os.getenv('INSTAGRAM_PASS')
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")  # Execução sem interface
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.service = Service('/usr/bin/chromedriver')
        self.driver = None

    def login(self):
        try:
            self.driver = webdriver.Chrome(service=self.service, options=self.chrome_options)
            self.driver.get("https://www.instagram.com/accounts/login/")
            time.sleep(2)
            
            # Preencher login
            username_input = self.driver.find_element(By.NAME, "username")
            username_input.send_keys(self.username)
            
            password_input = self.driver.find_element(By.NAME, "password")
            password_input.send_keys(self.password)
            password_input.send_keys(Keys.RETURN)
            time.sleep(5)
            
            return True
        except Exception as e:
            logging.error(f"Erro no login: {str(e)}")
            return False

    def post_status_update(self, message):
        if not self.login():
            return False
            
        try:
            # Clicar no botão 'Criar'
            self.driver.find_element(By.XPATH, "//div[text()='Criar']").click()
            time.sleep(2)
            
            # Selecionar 'Postagem'
            self.driver.find_element(By.XPATH, "//div[text()='Postagem']").click()
            time.sleep(2)
            
            # Escrever legenda
            caption = self.driver.find_element(By.TAG_NAME, "textarea")
            caption.send_keys(message)
            time.sleep(1)
            
            # Publicar
            self.driver.find_element(By.XPATH, "//div[text()='Compartilhar']").click()
            time.sleep(5)
            
            return True
        except Exception as e:
            logging.error(f"Erro ao postar: {str(e)}")
            return False
        finally:
            if self.driver:
                self.driver.quit()

# Exemplo de uso:
# notifier = InstagramNotifier()
# notifier.post_status_update("📊 Bot operando normalmente - Último trade: BTC +1.2%")