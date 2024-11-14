import os
import subprocess

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from datetime import datetime
from dotenv import load_dotenv
import json
import tabula
import tabula.errors

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
    rejectCookieButton = driver.find_element(By.CLASS_NAME, 'cky-btn-reject')
    userInput.send_keys(username)
    passwordInput.send_keys(password)
    rejectCookieButton.click()
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


def parsePfi(jsonFile='pfi.json'):
    with open(jsonFile) as f:
        data = json.load(f)
    totalAmount = data['totalAmount']
    expenses = data['expenses']
    sumExpenses = 0
    for key, value in expenses.items():
        sumExpenses += value
    if sumExpenses > totalAmount:
        raise ValueError('The sum of the expenses is greater than the total amount')
    return totalAmount, expenses


def parsePdf():
    """
    Function that parses the pfi pdf in order to provide a json parsable by parsePfi() function
    :return: Nothing, but it generate a json file "pfi_parsable.json"
    """

    # In questo dizionario ci saranno solo le stringhe diverse, il resto si fa tramite toLower :)
    conversion_dictionary = {"ALLOGGIO E\rUTENZE": "Affitti e utenze", "VIAGGI DI STUDIO": "Viaggi",
                             "MATERIALI\rDIDATTICI": "Materiale", "EVENTI\rCULTURALI": "Eventi",
                             "ELETTRONICA": "Strumenti elettronici"}
    try:
        tabula.convert_into("pfi.pdf", "pfi_converted.json", lattice=True, output_format="json", pages=1)
    except FileNotFoundError:
        print("Can't find pfi.pdf file")
        return
    except tabula.errors.JavaNotFound:
        print("Can't find java, please install it.")
        return
    except subprocess.CalledProcessError:
        print("Tabula execution failed")
        return
    # The json exist, so i'm gonna process it as the parsePfi() wants it.
    with open('pfi_converted.json') as f:
        data = json.load(f)[0]['data'][1:]  # terribile ma mi serve solo il sottoarray data dal secondo elemento in poi
    print(data)
    # riempio il dizionario expenses con i dati che mi interessano
    totalAmount = float(data[-1][1]['text'].lstrip('€ ').replace(',','.'))
    expenses = {}
    data = data[:-1]

    for item in data:
        if item[0]['text'] in conversion_dictionary:
            category = conversion_dictionary.get(item[0]['text'])
        else:
            category = item[0]['text'].capitalize()
        expenses[category] = float(item[1]['text'].lstrip('€ ').replace(',','.'))

    allowedAmount = [3000, 3800, 8000]
    minIndex = 0
    minValue = allowedAmount[0]
    for index, item in enumerate(allowedAmount):
        tmp = abs(totalAmount - item)
        if tmp<minValue:
            minIndex = index
            minValue = tmp

    totalAmount = allowedAmount[minIndex]
    with open('pfi.json','w') as f:
        json.dump({'totalAmount': totalAmount, 'expenses':expenses}, f)



def soldiRimanenti():
    """
    Faccio questa funzione perchè mi ritrovo sempre soldi in avanzo quando devo rendicontare a settembre.
    """
    df = pd.read_excel("currentYearAmount.xlsx")
    df = df.sort_values(by=["Tipo"]).reset_index(drop=True)  # ho il file ordinato per tipo
    # da qui in poi devo trovarmi i totali per tipo
    importoTot = []
    tipoTot = []
    importo = df['Importo']
    tipo = df['Tipo']

    currentType = tipo[0]
    sommaParz = 0
    for i in range(0, importo.size):
        if currentType != tipo[i]:
            tipoTot.append(currentType)
            importoTot.append(sommaParz)
            currentType = tipo[i]
            sommaParz = 0
        sommaParz += importo[i]
    if currentType == tipo[tipo.size - 1]:
        tipoTot.append(currentType)
        importoTot.append(sommaParz)
    totalDf = pd.DataFrame(columns=['Tipo', 'Importo'])
    totalDf['Tipo'] = tipoTot
    totalDf['Importo'] = importoTot

    # mi serve calcolare la differenza fra il pfi e ciò che ho rendicontato
    # parse pfi
    try:

        totalAmount, pfi = parsePfi()

        # tolgo le categorie == 0
        pfi = [(k, v) for k, v in pfi.items() if v != 0]
        # creo il dataframe del piano spese
        pfiDf = pd.DataFrame(pfi, columns=['Tipo', 'Importo'])
        pfiDf = pfiDf.sort_values(by=['Tipo']).reset_index(drop=True)

        # aggiungo le categorie che ancora non sono state rendicontate
        res = pd.DataFrame(columns=['Tipo', 'Importo'])
        res['Tipo'] = pd.concat([pfiDf['Tipo'], totalDf['Tipo']]).drop_duplicates(keep=False)
        res['Importo'] = 0
        totalDf = pd.concat([totalDf, res])
        totalDf = totalDf.sort_values(by=['Tipo']).reset_index(drop=True)
        # print(totalDf)
        # faccio la differenza per capire quanti soldi mancano da rendicontare
        diff = pfiDf.copy()
        diff['Importo'] = pfiDf['Importo'] - totalDf['Importo']
        diff.to_excel("moneyToSpend.xlsx")
        # calcolo il totale
        total = diff['Importo'].sum()
        if total > (totalAmount * 0.1):
            print("Finisci la rendicontazione fava")
        print(f"Mancante: {total}")
    except ValueError as e:
        print("An error occured during parsing of pfi (pfi.json)")
        print(e)


if __name__ == '__main__':
    parsePdf()
    #scraper()
    #soldiRimanenti()

