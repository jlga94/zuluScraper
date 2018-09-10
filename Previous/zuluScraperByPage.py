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


def getDataPerTrader(driver,ubications):
	data = {}
	for ubication in ubications.keys():
		if ubications[ubication]["Boolean"]:
			data[ubication] = len(driver.find_elements_by_xpath(ubications[ubication]["XPATH"])) > 0
		else:
			elementsFound = driver.find_elements_by_xpath(ubications[ubication]["XPATH"])
			if len(elementsFound) > 0:
				element = elementsFound[0]
				if "Attribute" in ubications[ubication].keys():
					data[ubication] = element.get_attribute(ubications[ubication]["Attribute"])
				else:
					if ubications[ubication]["Previous"]:
						element = element.find_element_by_xpath('..')
						element = element.find_element_by_xpath('..')
					data[ubication] = element.text.split('\n')[-1].strip()
			else:
				data[ubication] = 'Not Found'
	print(data)
	return data


def getDataPerTraderPerTime(data,driver,ubications):
	for ubication in ubications.keys():
		element = driver.find_element_by_xpath(ubications[ubication]["XPATH"])
		element = element.find_element_by_xpath('..')
		data[ubication] = element.text.split('\n')[-1].strip()
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

	columnsFile = "ubicationColumnsPageByPage.json"
	firefoxDirectory = r'D:\Navegadores\Mozilla Firefox\firefox.exe'

	today = datetime.datetime.strftime(datetime.datetime.now(), '%Y_%m_%d')
	createTodayDirectory(today)

	columnsJson = getColumns(columnsFile)

	timePeriods = [10000,30,90,180,365]
	timePeriodsNames = {30:"Month",90:"Trimester",180:"Semester",365:"Year",10000:"Total"}
	timePeriodsFilenames = {}

	for timePeriod in timePeriods:
		outputFile = "zulutrade_" + timePeriodsNames[timePeriod] + "_" + today + ".csv"
		timePeriodsFilenames[timePeriod] = outputFile
		writeHeaderFile(outputFile,columnsJson["Columns"])

	options = Options()
	options.add_argument("--headless")

	profile = webdriver.FirefoxProfile()
	profile.set_preference("dom.disable_beforeunload", True)

	profile.set_preference("browser.tabs.remote.autostart", False)
	profile.set_preference("browser.tabs.remote.autostart.1", False)
	profile.set_preference("browser.tabs.remote.autostart.2", False)
	profile.set_preference("browser.tabs.remote.force-enable", False)

	profile.set_preference("browser.cache.disk.enable", False)
	profile.set_preference("browser.cache.memory.enable", False)
	profile.set_preference("browser.cache.offline.enable", False)
	profile.set_preference("network.http.use-cache", False)

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
	driver.set_page_load_timeout(500)

	driver.get(urlLogin)

	userElement = driver.find_element_by_id("main_tbUsername")
	passwordElement = driver.find_element_by_id("main_tbPassword")

	userElement.send_keys(user)
	passwordElement.send_keys(password)

	driver.find_element_by_id("main_btnLogin").click()

	delayLogin = 30 #seconds
	delay = 180 #seconds

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

	#Filter By ZuluRank
	filterElement = driver.find_element_by_xpath("//zl-performance-forex-view/button")
	filterElement.click()

	termElement = driver.find_element_by_xpath("//zl-performance-forex//zl-timeframes/ngl-picklist/div/button")
	termElement.click()
	termOptionsElements = driver.find_elements_by_xpath("//zl-performance-forex//zl-timeframes/ngl-picklist/div/div/ul/li")
	termOptionsElements[-1].click()

	orderByElement = driver.find_element_by_xpath("//zl-performance-forex-sort-by/ngl-picklist/div/button")
	orderByElement.click()
	orderByOptionsElements = driver.find_elements_by_xpath("//zl-performance-forex-sort-by/ngl-picklist/div/div/ul/li")
	orderByOptionsElements[-1].click()

	orderByAscDescElement = driver.find_element_by_xpath("//zl-performance-forex-search/ngl-modal//select/option[@value='asc']")
	orderByAscDescElement.click()

	searchElement = driver.find_element_by_xpath("//zl-performance-forex-search//div/button[contains(text(),'Buscar')]")
	searchElement.click()

	try:
		element = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.XPATH,'//zl-load-more/button')))
	except TimeoutException:
		print("Se excedió el tiempo de espera")
		driver.quit()
		raise Exception()

	moreDetailElement = driver.find_elements_by_xpath("//zl-performance/div/div/div/div/button")
	print(len(moreDetailElement))

	moreDetailElement[0].click()


	rowsElements = driver.find_elements_by_xpath("//zl-performance-forex-list/div/table/tbody")
	
	firstRowElement = rowsElements[0].find_element_by_xpath(".//zl-username/a")
	urlTrader = firstRowElement.get_attribute("href")
	urlTrader = urlTrader.split("?")[0]
	
	maxTraders = 100

	for iTrader in range(maxTraders):
		print(iTrader)

		excelFilename = "No hay archivo Excel disponible"
		for timePeriod in timePeriods:
			print("TimePeriod: " + str(timePeriod))
			driver.get(urlTrader + "?t=" + str(timePeriod))

			try:
				element = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.XPATH,'//zl-timeframes/ngl-picklist/div/button')))
			except TimeoutException:
				print("Se excedió el tiempo de espera")
				driver.quit()
				raise Exception()

			sleep(2.5)

			rowData = getDataPerTrader(driver,columnsJson["UbicationsGeneral"])
			rowData["Url"] = urlTrader + "?t=" + str(timePeriod)

			badgesElementsHTML = driver.find_element_by_xpath("//zl-trader-badge").get_attribute('innerHTML')
			for badge,item in columnsJson["UbicationsBadges"].items():
				rowData[badge] = item["ICON"] in badgesElementsHTML

			rowData = getDataPerTraderPerTime(rowData,driver,columnsJson["UbicationsPerTime"])

			if timePeriodsNames[timePeriod] == "Total":
				if len(driver.find_elements_by_xpath("//zl-trading-history-excel-export/span/button")) > 0:
					exportExcelElement = driver.find_element_by_xpath("//zl-trading-history-excel-export/span/button")
					exportExcelElement.click()

					exportExcel2007Elements = driver.find_elements_by_xpath("//zl-trading-history-excel-export/span/div/ul/li")
					exportExcel2007Elements[0].click()

					sleep(3)

					excelFilename = getLastFilename(os.getcwd() + '\\' + today)

			rowData["Time"] = timePeriodsNames[timePeriod]
			rowData["Excel"] = excelFilename

			print(rowData)

			dfTraders = pd.DataFrame(rowData,columns=columnsJson["Columns"], index=[0])
			with open(timePeriodsFilenames[timePeriod], "a") as f:
				dfTraders.to_csv(f, header=None, index=False,encoding='ISO-8859-1', sep='|')

		#Get next link
		nextElement = driver.find_elements_by_xpath("//zl-trader-rank/div/a[contains(@title,'al siguiente trader')]")
		if len(nextElement)> 0:
			urlTrader = nextElement[0].get_attribute("href")
			urlTrader = urlTrader.split("?")[0]
		else:
			print("No hay Next Trader")
			break

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
	
