from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from contextlib import contextmanager
from selenium.webdriver.support.expected_conditions import staleness_of
import selenium

import re, time, datetime
from bs4 import BeautifulSoup
import csv, string, sys

from time import sleep
import pandas as pd

columns = ['TraderName','Pips','Operaciones','Roi','MediaPips','GananciaPorc','MaxDDPips','Semanas','Usuarios','CantidadSeguida','BeneficioSegCuentaReal']




def getDataPerTrader(html_source):
	soup = BeautifulSoup(html_source, 'lxml')

	nameElement = soup.find("a", {"class": "text-main zlds-link--brand"})



browser = None

urlLogin = "https://es.zulutrade.com/login"
urlToScrap = "https://es.zulutrade.com/traders"

user = "jose.gil@pucp.pe"
password = "recoleta11"


profile = webdriver.FirefoxProfile()
profile.set_preference("dom.disable_beforeunload", True)

profile.set_preference("browser.tabs.remote.autostart", False)
profile.set_preference("browser.tabs.remote.autostart.1", False)
profile.set_preference("browser.tabs.remote.autostart.2", False)

profile.set_preference("browser.tabs.remote.force-enable", False)

driver = webdriver.Firefox(firefox_profile = profile)

driver.get(urlLogin)

userElement = driver.find_element_by_id("main_tbUsername")
passwordElement = driver.find_element_by_id("main_tbPassword")

userElement.send_keys(user)
passwordElement.send_keys(password)


driver.find_element_by_id("main_btnLogin").click()


sleep(4)

driver.get(urlToScrap)
delay = 25 #seconds

'''
try:
	myElem = WebDriverWait(browser, delay).until(EC.presence_of_element_located((By.CLASS_NAME, 'zl-performance-table')))
except TimeoutException:
	print("Se excedió el tiempo de espera")
	driver.quit()
'''

sleep(10)

moreDetailElement = driver.find_elements_by_xpath("//button[@nglbutton='neutral']")
print(len(moreDetailElement))

moreDetailElement[0].click()


for i in range(9):

	downloadMoreElement = driver.find_element_by_xpath("//button[@class='slds-button slds-button--inverse']")
	downloadMoreElement.click()

	sleep(4.5)




rowsElements = driver.find_elements_by_xpath("//tbody[@class='large']")

for rowElement in rowsElements:

	rowData = getDataPerTrader(rowElement.get_attribute('innerHTML'))
