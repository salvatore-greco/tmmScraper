import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
url = 'https://www.tuttomeritomio.it/login'
username = os.getenv('TMM_USERNAME')
password = os.getenv('TMM_PASSWORD')

def scraper():
    df = pd.DataFrame(columns=['Causale', 'Tipo', 'Data', 'Importo'])
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
    driver.get(url)
    userInput = driver.find_element(By.ID, 'username-7')
    passwordInput = driver.find_element(By.ID, 'user_password-7')
    buttonSubmit = driver.find_element(By.ID, 'um-submit-btn')
    userInput.send_keys(username)
    passwordInput.send_keys(password)
    buttonSubmit.click()
    try:
        WebDriverWait(driver, 10).until(
            ec.url_to_be(f'https://www.tuttomeritomio.it/utente/{username}/')
        )
        navBar = driver.find_element(By.CLASS_NAME, 'um-profile-nav')
        refToRendicontazione = navBar.find_element(By.XPATH, 'div[4]/a[2]').get_attribute('href')
        driver.get(refToRendicontazione)
        WebDriverWait(driver, 10).until(
            ec.url_to_be(f'https://www.tuttomeritomio.it/utente/{username}/?profiletab=conto')
        )
        tableContainer = driver.find_element(By.CLASS_NAME, 'lista-rendicontazione')
        table = tableContainer.find_element(By.TAG_NAME, 'table').find_element(By.TAG_NAME, 'tbody')
        causale = []
        tipo = []
        data = []
        importo = []
        rows = table.find_elements(By.TAG_NAME, 'tr')
        for row in rows:
            columns = row.find_elements(By.TAG_NAME, 'td')
            causale.append(columns[0].text)
            tipo.append(columns[1].text)
            data.append(columns[2].text)
            importo.append(columns[3].text)
        df['Causale'] = causale
        df['Tipo'] = tipo
        df['Data'] = data
        df['Importo'] = importo
        df['Importo'] = df['Importo'].replace({'€': '', r'\.': '', r',': '.'}, regex=True)
        df['Importo'] = pd.to_numeric(df['Importo'])
        df['Data'] = pd.to_datetime(df['Data'], format='%Y-%m-%d')
        lastYear = datetime.now().year - 1
        filteredDf = df[(df['Data'] > f'{lastYear}-09-30')]
        filteredDf.to_excel('currentYearAmount.xlsx')
        df.to_excel('allAmount.xlsx')
    finally:
        driver.quit()

if __name__ == '__main__':
    scraper()