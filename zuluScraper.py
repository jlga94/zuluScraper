from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from contextlib import contextmanager
from selenium.webdriver.support.expected_conditions import staleness_of
import selenium
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

import re, time, datetime
from bs4 import BeautifulSoup
import csv, string, sys, json

from time import sleep
import datetime
import pandas as pd
import os, sys, time, datetime
import shutil, glob

class LoginException(Exception):
	def __init__(self):
		Exception.__init__(self,"Usuario o Password incorrectos")

def getColumns(columnsFile):
	with open(columnsFile, "r") as f:
		return json.load(f)


def createTodayDirectory(todayDirectory):
	if os.path.exists(todayDirectory):
		shutil.rmtree(todayDirectory)
	os.makedirs(todayDirectory)


def getLastFilename(path):
	list_of_files = glob.glob(path + '/*')
	latest_file = max(list_of_files, key=os.path.getctime)
	return latest_file


def getDataPerTrader(rowElement,ubications):
	data = {}
	for ubication in ubications.keys():
		element = rowElement.find_element_by_xpath(ubications[ubication]["XPATH"])
		if "Attribute" in ubications[ubication].keys():
			data[ubication] = element.get_attribute(ubications[ubication]["Attribute"])
		else:
			element = element.find_element_by_xpath('..')
			data[ubication] = element.text.split('\n')[1].strip()

	print(data)
	return data


def getDataInsidePagePerTrader(data,driver,ubications):
	for ubication in ubications.keys():
		if ubications[ubication]["Boolean"]:
			data[ubication] = len(driver.find_elements_by_xpath(ubications[ubication]["XPATH"])) > 0
		else:
			data[ubication] = driver.find_element_by_xpath(ubications[ubication]["XPATH"]).text.strip()

	print(data)
	return data


def writeHeaderFile(outputFile,columns):
	dfTraders = pd.DataFrame(columns=columns)

	#Write CSV file header
	with open(outputFile, "w") as f:
		dfTraders.to_csv(f, header=True, index=False,encoding='ISO-8859-1', sep='|')

def main(user,password):
	urlRoot = "https://es.zulutrade.com"
	urlLogin = "https://es.zulutrade.com/login"
	urlToScrap = "https://es.zulutrade.com/traders"

	columnsFile = "ubicationColumns.json"
	firefoxDirectory = r'D:\Navegadores\Mozilla Firefox\firefox.exe'

	today = datetime.datetime.strftime(datetime.datetime.now(), '%Y_%m_%d')
	createTodayDirectory(today)

	outputFile = "zulutrade_" + today + ".csv"

	columnsJson = getColumns(columnsFile)

	writeHeaderFile(outputFile,columnsJson["Columns"])

	options = Options()
	options.add_argument("--headless")

	profile = webdriver.FirefoxProfile()
	profile.set_preference("dom.disable_beforeunload", True)

	profile.set_preference("browser.tabs.remote.autostart", False)
	profile.set_preference("browser.tabs.remote.autostart.1", False)
	profile.set_preference("browser.tabs.remote.autostart.2", False)
	profile.set_preference("browser.tabs.remote.force-enable", False)

	profile.set_preference('browser.download.folderList', 2) # custom location
	profile.set_preference('browser.download.manager.showWhenStarting', False)
	profile.set_preference('browser.download.dir', os.getcwd()+ '\\' + today)
	profile.set_preference('browser.helperApps.neverAsk.saveToDisk', "application/xml,text/xml,application/csv,application/excel,application/vnd.msexcel,application/vnd.ms-excel,text/anytext,text/comma-separated-values,text/csv,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/octet-stream")
	profile.set_preference("browser.helperApps.neverAsk.openFile","application/xml,text/xml,application/csv,application/excel,application/vnd.msexcel,application/vnd.ms-excel,text/anytext,text/comma-separated-values,text/csv,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/octet-stream")
	profile.set_preference("browser.helperApps.alwaysAsk.force", False)
	profile.set_preference("browser.download.manager.useWindow", False)
	profile.set_preference("browser.download.manager.focusWhenStarting", False)
	profile.set_preference("browser.download.manager.alertOnEXEOpen", False)
	profile.set_preference("browser.download.manager.showAlertOnComplete", False)
	profile.set_preference("browser.download.manager.closeWhenDone", True)

	binary = FirefoxBinary(firefoxDirectory)

	driver = webdriver.Firefox(firefox_options=options,firefox_profile = profile,firefox_binary=binary)
	#driver = webdriver.Firefox(firefox_profile = profile,firefox_binary=binary)
	#driver = webdriver.Firefox(firefox_profile = profile)

	driver.get(urlLogin)

	userElement = driver.find_element_by_id("main_tbUsername")
	passwordElement = driver.find_element_by_id("main_tbPassword")

	userElement.send_keys(user)
	passwordElement.send_keys(password)


	driver.find_element_by_id("main_btnLogin").click()

	delayLogin = 30 #seconds
	delay = 90 #seconds

	try:
		element = WebDriverWait(driver, delayLogin).until(EC.presence_of_element_located((By.ID,'user-top-container')))
	except TimeoutException:
		print("Se excedió el tiempo de espera")
		driver.quit()
		raise LoginException()

	driver.get(urlToScrap)
	
	try:
		element = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.XPATH,'//zl-load-more/button')))
	except TimeoutException:
		print("Se excedió el tiempo de espera")
		driver.quit()
		raise Exception()

	moreDetailElement = driver.find_elements_by_xpath("//zl-performance/div/div/div/div/button")
	print(len(moreDetailElement))

	moreDetailElement[0].click()


	for i in range(59):
		print("Page: " + str(i))
		try:
			element = WebDriverWait(driver, delayLogin).until(EC.presence_of_element_located((By.XPATH,'//zl-load-more/button')))
		except TimeoutException:
			print("Se excedió el tiempo de espera del boton de Cargar mas")
			break

		if len(driver.find_elements_by_xpath("//zl-load-more/button")) > 0:
			downloadMoreElement = driver.find_element_by_xpath("//zl-load-more/button")
			downloadMoreElement.click()
		else:
			break

		#sleep(4.5)


	rowsElements = driver.find_elements_by_xpath("//zl-performance-forex-list/div/table/tbody")
	print(len(rowsElements))

	#badgesElements = driver.find_elements_by_xpath("//zl-trader-badge")
	#print(len(badgesElements))

	for iRowElement in range(len(rowsElements)):
		print(iRowElement)
		rowData = getDataPerTrader(rowsElements[iRowElement],columnsJson["UbicationsGrid"])

		'''
		numElements = len(badgesElements[iRowElement].find_elements_by_xpath(".//ngl-icon[@ng-reflect-set-icon='icon-badge-partially-verified' or @ng-reflect-set-icon='icon-badge-fully-verified']"))
		print(numElements)

		if numElements > 0:
			print("Si hay elemento Check")
			checkIconElement = badgesElements[iRowElement].find_elements_by_xpath(".//ngl-icon[@ng-reflect-set-icon='icon-badge-partially-verified' or @ng-reflect-set-icon='icon-badge-fully-verified']")[numElements - 1]
			
			driver.execute_script("arguments[0].scrollIntoView();", rowsElements[iRowElement])
			
			hover = ActionChains(driver).move_to_element(checkIconElement)
			hover.perform()

			sleep(2)

			soup = BeautifulSoup(driver.page_source, 'lxml')
			popUpElement = soup.find("zl-trader-verification-popover")
			#print(popUpElement)

			#To get lost of Focus of the little windows to iterate the next row
			hover = ActionChains(driver).move_to_element(badgesElements[iRowElement])
			hover.perform()
			sleep(1)
		'''

		badgesElementsHTML = rowsElements[iRowElement].find_element_by_xpath(".//zl-trader-badge").get_attribute('innerHTML')

		for badge,item in columnsJson["UbicationsBadges"].items():
			rowData[badge] = item["ICON"] in badgesElementsHTML


		#open tab
		driver.find_element_by_tag_name('body').send_keys(Keys.CONTROL + 't')

		print(driver.window_handles)


		driver.switch_to.window(driver.window_handles[1])

		driver.get(rowData["Url"])

		try:
			element = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.XPATH,'//zl-timeframes/ngl-picklist/div/button')))
		except TimeoutException:
			print("Se excedió el tiempo de espera")
			driver.quit()
			raise Exception()

		rowData = getDataInsidePagePerTrader(rowData, driver, columnsJson["UbicationsInside"])

		graphicTimeElement = driver.find_element_by_xpath("//zl-timeframes/ngl-picklist/div/button")
		graphicTimeElement.click()

		graphicTotalTimeElements = driver.find_elements_by_xpath("//zl-timeframes/ngl-picklist/div/div/ul/li")
		graphicTotalTimeElements[len(graphicTotalTimeElements) - 1].click()

		excelFilename = "No hay archivo Excel disponible"

		if len(driver.find_elements_by_xpath("//zl-trading-history-excel-export/span/button")) > 0:
			exportExcelElement = driver.find_element_by_xpath("//zl-trading-history-excel-export/span/button")
			exportExcelElement.click()

			exportExcel2007Elements = driver.find_elements_by_xpath("//zl-trading-history-excel-export/span/div/ul/li")
			exportExcel2007Elements[0].click()

			sleep(3)

			excelFilename = getLastFilename(os.getcwd() + '\\' + today)

		rowData["Excel"] = excelFilename

		print(rowData)

		dfTraders = pd.DataFrame(rowData,columns=columnsJson["Columns"], index=[0])
		with open(outputFile, "a") as f:
			dfTraders.to_csv(f, header=None, index=False,encoding='ISO-8859-1', sep='|')

		# close the tab
		driver.find_element_by_tag_name('body').send_keys(Keys.CONTROL + 'w') 


		driver.switch_to.window(driver.window_handles[0])

	driver.quit()


if __name__ == "__main__":
	try:
		user = sys.argv[1]
		password = sys.argv[2]
		print("User: "+ user)
		print("Password: "+ password)
		t0 = time.time()
		main(user,password)
		tf = time.time()
		total_time = int(tf - t0)
		print("Tiempo Ejecución Total: " + str(datetime.timedelta(seconds=total_time)))
	except LoginException:
		print("Usuario o Password Incorrectos")
	#except:
	#	print("Unexpected error:", sys.exc_info())
	
