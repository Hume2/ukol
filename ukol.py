from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import psycopg2
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

host = "localhost"
database = "flats"
user = "ukol"
password = "heslo"
port = 5432
num_flats = 500

conn = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)

cur = conn.cursor()
print('PostgreSQL database version:')
cur.execute('SELECT version()')

# display the PostgreSQL database server version
db_version = cur.fetchone()
print(db_version)
print("")

cur.execute("SELECT * FROM information_schema.tables WHERE table_name='flats'")
if cur.rowcount:
	print("Database already exists.")
else:
	cur.execute("""CREATE TABLE flats (
		id INTEGER PRIMARY KEY,
		name VARCHAR(256) NOT NULL,
		link VARCHAR(256) NOT NULL,
		locality VARCHAR(256) NOT NULL,
		price VARCHAR(256) NOT NULL,
		img VARCHAR(256) NOT NULL
	)""")

	cur.close()
	conn.commit()

	fetch = Fetcher()
	for i in range(0, num_flats):
		f = fetch.load_entry()
		cur = conn.cursor()
		print("fetching flat %d/%d"%(i, num_flats), end="\r")
		cur.execute("INSERT INTO flats(id, name, link, locality, price, img) VALUES (%s,%s,%s,%s,%s,%s)",
			     (i, f.name, f.link, f.locality, f.price, f.img))
		cur.close()
		conn.commit()
	fetch.close()
	print("fetching done")

print("reading database")
cur.execute("SELECT name, link, locality, price, img FROM flats ORDER BY id ASC")
rc = cur.rowcount
flats = []
row = cur.fetchone()
while row is not None:
	flats.append(Flat(*row))
	row = cur.fetchone()
print(make_html(flats))

conn.close()
