from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import time

class Flat:
	def __init__(self, name, link, locality, price, img):
		self.name = name
		self.link = link
		self.locality = locality
		self.price = price
		self.img = img
	
	def as_html(self):
		return "<tr><td><img src=\""+self.img+"\"></td><td><a href=\""+self.link+"\">"+self.name+"</a></td><td>"+self.locality+"</td><td>"+self.price+"</td></tr>"

class Fetcher:
	def __init__(self):
		self.driver = webdriver.Firefox()
		self.options = webdriver.FirefoxOptions()
		self.options.set_preference("javascript.enabled", True)
		self.driver.get("https://www.sreality.cz/hledani/prodej/byty?strana=1")
		time.sleep(5)
		self.load_page(1)
	
	def load_page(self, page):
		self.driver.get("https://www.sreality.cz/hledani/prodej/byty?strana=%d"%(page))
		WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[@class=\"property ng-scope\"]")))
		self.page = page
		self.entries = self.driver.find_elements(By.XPATH, "//div[@class=\"property ng-scope\"]")
		self.at = 0
	
	def load_entry(self):
		if self.at >= len(self.entries):
			self.load_page(self.page + 1)
		entry = self.entries[self.at]
		self.at = self.at+1
		img = entry.find_element(By.XPATH, ".//a/img").get_attribute("src")
		link = entry.find_element(By.XPATH, ".//h2/a").get_attribute("href")
		name = entry.find_element(By.XPATH, ".//h2").text
		locality = entry.find_element(By.XPATH, ".//span[@class=\"locality ng-binding\"]").text
		price = entry.find_element(By.XPATH, ".//span[@class=\"price ng-scope\"]").text
		return Flat(name, link, locality, price, img)
	
	def close(self):
		self.driver.close()

def make_html(flats):
	result = "<html><body><table border=1><tr><th>Obrázek</th><th>Název</th><th>Lokalita</th><th>Cena</th></tr>\n"
	for f in flats:
		result = result + f.as_html() + "\n"
	result = result + "</table></body></html>"
	return result

fetch = Fetcher()
flats = []
for i in range(0, 500):
	flats.append(fetch.load_entry())
fetch.close()
print(make_html(flats))

