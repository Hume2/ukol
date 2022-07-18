from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import psycopg2
from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import argparse

print("Server started!")

class Flat:
	def __init__(self, name, link, locality, price, img):
		self.name = name
		self.link = link
		self.locality = locality
		self.price = price
		self.img = img
	
	def as_html(self):
		return "<tr><td><img src=\""+self.img+"\"></td><td><a href=\""+self.link+"\">"+self.name+"</a></td><td>"+self.locality+"</td><td>"+self.price+"</td></tr>\n"


class Fetcher:
	def __init__(self):
		print("Starting Firefox")
		self.options = webdriver.FirefoxOptions()
		self.options.add_argument("--headless")
		self.options.set_preference("javascript.enabled", True)
		self.driver = webdriver.Firefox(options=self.options)
		self.driver.get("https://www.sreality.cz/hledani/prodej/byty?strana=1")
		print("Getting around the cookies stuff...")
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


class MyHTTPServer(BaseHTTPRequestHandler):
	def do_GET(self):
		self.send_response(200)
		self.send_header("Content-type", "text/html")
		self.end_headers()
		self.wfile.write(bytes("<html><head><meta charset=\"UTF-8\"></head><body>\n", "utf-8"))
		self.wfile.write(bytes("<table border=1><tr><th>Obrázek</th><th>Název</th><th>Lokalita</th><th>Cena</th></tr>", "utf-8"))
		global conn
		cur = conn.cursor()
		cur.execute("SELECT name, link, locality, price, img FROM flats ORDER BY id ASC")
		rc = cur.rowcount
		flats = []
		row = cur.fetchone()
		while row is not None:
			flat = Flat(*row)
			self.wfile.write(bytes(flat.as_html(), "utf-8"))
			row = cur.fetchone()
		self.wfile.write(bytes("</table></body></html>", "utf-8"))
		cur.close()

parser = argparse.ArgumentParser(description="Fetch data from sreality.cz and display them in a HTTP server.")
parser.add_argument("--database", default="db", nargs="?",
                    help="The name of the postgreSQL database to connect to.")
parser.add_argument("--user", default="user", nargs="?",
                    help="The postgreSQL username.")
parser.add_argument("--password", default="pass", nargs="?",
                    help="The password for the given username.")
parser.add_argument("-s", "--host", nargs="?", default="postgres",
                    help="The IP adress of the postgreSQL database.")
parser.add_argument("-p", "--port", type=int, nargs="?", default=5432,
                    help="The port of the postgreSQL database.")
parser.add_argument("-u", "--update", action="store_const", const=True, default=False,
                    help="Update the database even though it already exists.")

args = parser.parse_args()
host = args.host
database = args.database
user = args.user
password = args.password
port = args.port
update = args.update
num_flats = 500

conn = None
while True:
	try:
		conn = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
		break
	except:
		time.sleep(0.01)
		print("reaching postgreSQL server...")
cur = conn.cursor()

def create_db():
	global conn
	cur = conn.cursor()
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

cur.execute("SELECT * FROM information_schema.tables WHERE table_name='flats'")
if cur.rowcount:
	if update:
		print("The database will be updated.")
		cur.execute("DROP TABLE flats")
		cur.close()
		create_db()
		conn.commit()
	else:
		print("Using existing database. Use -u to update the database.")
		cur.close()
else:
	print("The database was not found. It will be created.")
	create_db()
	cur.close()

webServer = HTTPServer(("localhost", 8080), MyHTTPServer)
print("Server started. Press Ctrl+C to stop.")
for i in range(0, 100):
	print("----------------------------------------------------------------------")
try:
	webServer.serve_forever()
except KeyboardInterrupt:
	pass

webServer.server_close()
conn.close()
print("Server stopped.")
