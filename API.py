from bs4 import BeautifulSoup
import urllib3
import re
from flask import Flask, jsonify
from flask_cors import CORS, cross_origin
import os
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait



EXPOSE_URL = "https://www.immobilienscout24.de/expose/{}#"
BASE_URL = 'https://www.immobilienscout24.de/Suche/de/baden-wuerttemberg/karlsruhe-kreis/haus-kaufen?enteredFrom=result_list'
app = Flask(__name__)
app.config['CORS_HEADERS'] = 'Content-Type'
cors = CORS(app, resources={r"*": {"origins": os.environ.get('WEB')}})
driver = webdriver.Remote(os.environ.get('BROWSER'), DesiredCapabilities.FIREFOX)
@app.route('/')
def GetListingsRoute():
    result = GetListings()
    return jsonify(result)

def GetListings():
  http = urllib3.PoolManager()
  page = http.request("GET", BASE_URL)
  soup = BeautifulSoup(page.data, features="lxml")

  listings_list = soup.find("ul", id="resultListItems")
  listings_items_unfiltered = listings_list.findChildren("li", recursive=False)

  listings_items = []
  for x in listings_items_unfiltered:
    try:
      listings_items.append(x["data-id"])
    except Exception as e:
      pass


  results = []

  for x in listings_items[0:5]:
    try:
      http = urllib3.PoolManager()
      page = http.request("GET", EXPOSE_URL.format(x))
      soup = BeautifulSoup(page.data, features="lxml")

      # find the class marker
      # price_div is easy to find, and thus easy to find the marker
      main_div = soup.find('div', class_="main-criteria-container")
      price_div = (main_div.findChild('div').findChild('div').findChild('div'))
      class_marker = price_div.findChild('div')["class"][0].split('-')[0] + '-{}'

      try:
        provision = soup.find('dd', class_=class_marker.format('provision')).text
        provision = re.search(r'[0-9,]*[0-9]', provision).group()
        provision = provision.replace(',', '.')
        provision = float(provision)

      except Exception as e:
        provision = 0

      try:
        price = soup.find('div', class_=class_marker.format('kaufpreis')).text
        price = re.search(r'[0-9.]*[0-9]', price).group().replace('.', '')
        price = int(price)

      except Exception as e:
        price = 0

      try:
        size = soup.find('div', class_=class_marker.format('wohnflaeche')).text
        size = re.search(r'\d+', size).group()
        size = int(size)

      except Exception as e:
        size = 0

      try:
        img = soup.find('img', class_="gallery-element")
        src = img['src']

      except Exception as e:
        src = ''

      try:
        driver.get(EXPOSE_URL.format(x))
        monthly = WebDriverWait(driver,10).until(
              lambda x: x.find_element_by_xpath("//p[@class='average-rates-monthly-rate']"))
        monthly = int(monthly.text.split(' ')[0].replace('.', ''))

      except Exception as e:
        monthly = ''

      result = {}
      result['url'] = EXPOSE_URL.format(x)
      result['src'] = src
      result['provision'] = provision
      result['price'] = price
      result['size'] = size
      result['monthly'] = monthly

      results.append(result)


    except Exception as e:
      print(x)

  return results

if __name__ == "__main__":
  print(GetListings())

  '''
  http = urllib3.PoolManager()
  page = http.request("GET", 'https://www.immobilienscout24.de/expose/121136183#/')
  soup = BeautifulSoup(page.data, features="lxml")
  print(soup)
  a = soup.find('div', class_="offers-content")
  print(a)
  '''

