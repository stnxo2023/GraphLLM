#!/usr/bin/python3

# come ho generato firefox:
## creato un profilo dedicato
## installato ublock origin e tutti i filtri
## ???
## profit


from selenium import webdriver 
from selenium.webdriver.chrome.options import Options
import time
import tempfile

from selenium.webdriver.firefox.webdriver import Service

from selenium import webdriver

import inspect
import os
import sys
from os.path import expanduser, exists

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

sys.path.insert(0,currentdir)
os.environ["PATH"] +=":"+currentdir

# try:
#     from . import scraper_utils
# except:
    #import scraper_utils
import scraper_utils


#url="https://en.m.wikipedia.org/wiki/Piston"
#url="https://www.ilpost.it/2024/04/26/prezzi-variabili-opachi/"
#url="https://admiralcloudberg.medium.com/fire-in-the-fog-the-crash-of-swissair-flight-306-c54893961151"
#url="https://arstechnica.com/science/2024/04/metafluid-gives-robotic-gripper-a-soft-touch/"
url="https://www.reddit.com/r/italy/?feedViewType=compactView"

url="https://news.ycombinator.com/"

if len(sys.argv) > 1:
  url = sys.argv[1]

debug_mode = False

if(len(sys.argv) > 1):
    url = sys.argv[1]

print("loading additional scripts", file=sys.stderr)

f = open(currentdir +"/removeHiddenNodes.js","r")
script_removeHiddenNodes = f.read()
f.close()

f = open(currentdir +"/Readability.js","r")
scr = f.read()
f.close()

f = open(currentdir +"/fetchWrapper.js","r")
fetch_wrapper = f.read()
f.close()

# this is  executed just before appying readability.js
f = open(currentdir +"/redditFixer.js","r")
reddit_fixer = f.read()
f.close()

f = open(currentdir +"/Readability-readerable.js","r")
readerable = f.read()
f.close()

driver = None

class Scraper():
    def __init__(self):
        self.driver = None
        self.debug_mode = debug_mode

    def _applyScript(self,script_name):
        f = open(currentdir + "/" + script_name, "r")
        s = f.read()
        f.close()
        retVal = self.driver.execute_script(s)
        return retVal

    def initialize_driver(self):
        service = Service()
        options = webdriver.FirefoxOptions()
        # options.add_argument('--safe-mode')
        if not debug_mode:
            options.add_argument('--headless')

        home_dir = expanduser("~")
        profile_path = home_dir + "/.mozilla/firefox/profile.bot"
        print("Loading the firefox profile", profile_path, file=sys.stderr)
        if not exists(profile_path):
            print("WARNING: profile not found. check the documentation.", profile_path, file=sys.stderr)

        try:
            profile = webdriver.FirefoxProfile(profile_path)
        except:
            print("profile.bot not found. Using default with degraded performance", file=sys.stderr)
            profile = webdriver.FirefoxProfile()

        options.profile = profile

        print("launching firefox via geckodriver", file=sys.stderr)

        try:
            self.driver = webdriver.Firefox(options=options, service=service)
        except:
            service.path = currentdir + "/geckodriver"
            if not exists(service.path):
              print("WARNING: geckodriver not found. download it and put it here.", service.path, file=sys.stderr)

            self.driver = webdriver.Firefox(options=options, service=service)

    def _wait_page_load(self):
        driver = self.driver

        # aspetto che il documento sia caricato
        while driver.execute_script("return document.readyState") != "complete":
            time.sleep(.1)


    def _wait_dynamic_components(self):
        driver = self.driver

        while driver.execute_script("return (window.jQuery != null) && (jQuery.active > 0);"):
            time.sleep(.1)

        if driver.execute_script("return window.running_fetches") > 0:
              h = [-1]*10
              # if no changes for 1 second or timeout of 10 seconds
              print("waiting for extra components to load (reddit?)", file=sys.stderr)
              for i in range(50):
                r = driver.execute_script("return window.running_fetches")
                h=h[1:]
                h.append(r)
                if h.count(h[0]) == len(h):
                  break
                #print(r, file=sys.stderr)
                time.sleep(.1)
              print("after wait, running:",r, file=sys.stderr)

    def load_page(self,url):
        driver=self.driver

        print("Started processing url: " + url, file=sys.stderr)

        start_url = "about:reader?url=" + url # not used anymore
        print("loading webpage", url,file=sys.stderr)

        driver.get(url)

        print("waiting for static components...", file=sys.stderr)
        self._wait_page_load()

        print("waiting for dynamic components...", file=sys.stderr)
        driver.execute_script(fetch_wrapper)
        self._wait_dynamic_components()

        print("Scrolling the page...", file=sys.stderr)
        for i in range(4):
            scrpt = """ let options = {top: (document.body.scrollHeight - window.innerHeight), left: 0, behavior: "smooth", }
            if (window.pageYOffset + window.innerHeight < document.body.scrollHeight) { window.scrollTo(options) }
            """
            driver.execute_script(scrpt)
            self._wait_dynamic_components()

        #print("Apply reddit fixes...", file=sys.stderr)
        #driver.execute_script(reddit_fixer)
        #self._wait_dynamic_components()

        print("Web page loaded.", file=sys.stderr)

        html_content = driver.page_source
        scraper_utils.write_file(tempfile.gettempdir() + "/pagina0.html", html_content)

        return driver.page_source

    def _apply_fixes(self):
        print("deleting nodes identified by ublock origin.", file=sys.stderr)
        self.driver.execute_script(script_removeHiddenNodes)

        self._applyScript("fixUnknownTags.js")

        self._applyScript("fixRelativeLinks.js")

        hostname = self.driver.current_url.split("//",1)[1].split("/")[0]
        if "reddit" in hostname:
            self._applyScript("redditFixer2.js")
        return self.driver.page_source

    def _isReaderable(self):
        should_keep = self.driver.execute_script(readerable + "\n" + "return isProbablyReaderable(document);")
        hostname = self.driver.current_url.split("//", 1)[1].split("/")[0]
        if "reddit" in hostname:
            should_keep = False

        print("reader mode available?", should_keep, file=sys.stderr)
        return should_keep

    def extract_content(self):
        driver = self.driver

        ## check


        ## readability per estrarre il contenuto
        pagina_rjs = driver.execute_script(scr + "\n" + "return new Readability(document.cloneNode(true)).parse();")

        # fallback if readability fails
        if (not debug_mode) and not pagina_rjs:
          driver.execute_script(scr + "\n" + "return new Readability(document).parse();")
          pagina_rjs = {}
          pagina_rjs["title"] = url
          pagina_rjs["content"] = driver.page_source
        scraper_utils.write_file(tempfile.gettempdir() + "/pagina1.html",str(pagina_rjs["content"]))



        html_content = driver.page_source

        #if not should_keep:
        #    pagina_rjs["content"] = html_content



        return pagina_rjs

    def close_driver(self):
        if not self.debug_mode:
          print("closing firefox", file=sys.stderr)
          self.driver.quit()




## carico i dati in bs per eventuali riprocessamenti
def clean_soup(content):
  print("clean soup", file=sys.stderr)
  #soup = BeautifulSoup(article["plain_content"], 'lxml')
  from bs4 import BeautifulSoup
  soup = BeautifulSoup(content, 'lxml')
  for s in soup.select('figure'):
      s.extract()
  for el in  soup.select('a[role="button"]'): #wikipedia [edit] links
      el.extract()
      
  for el in soup.select("shreddit-post>p[slot=title]"):
      el.extract()

  cleaned_content = str(soup)
  return cleaned_content
  
##converto in md
def convert_to_md(title, data):
  print("convert to md", file=sys.stderr)
  import html2text
  converter = html2text.HTML2Text()
  converter.ignore_links=False
  converter.ignore_images=True
  converter.protect_links = False
  converter.body_width = None
  markdown_content = "# " + title + "\n\n" + converter.handle(data).strip()
  scraper_utils.write_file(tempfile.gettempdir() + "/pagina.md",markdown_content)
  return markdown_content

def apply_static_readability(content):
  ## ora riparso e rimuovo i link
  import readabilipy
  print("static readability", file=sys.stderr)

  orig = readabilipy.simplifiers.html.elements_to_replace_with_contents
  def wrapper_replace():
      res = orig()
      res = [el for el in res if el != "a"]
      return res
  readabilipy.simplifiers.html.elements_to_replace_with_contents = wrapper_replace

  orig = readabilipy.simplifiers.html.block_level_whitelist
  def wrapper_replace():
      res = orig()
      res = ["a"] + res
      return res
  readabilipy.simplifiers.html.block_level_whitelist = wrapper_replace


  article = readabilipy.simple_json_from_html_string(content,use_readability=False)

  scraper_utils.write_file(tempfile.gettempdir() + "/pagina2.html",article["content"])

  conveted_static = convert_to_md(article["title"], article["content"])
  return conveted_static

def apply_dynamic_readability(scraper):
    pagina_rjs = scraper.extract_content()
    clean_html = clean_soup(pagina_rjs["content"])
    scraper_utils.write_file(tempfile.gettempdir() + "/pagina3.html", clean_html)
    markdown_content = convert_to_md(pagina_rjs["title"], clean_html)
    return markdown_content

def scrape(url):
  scraper = Scraper()
  scraper.initialize_driver()
  scraper.load_page(url)
  html_content = scraper._apply_fixes()

  static_parsed = apply_static_readability(html_content)
  dynamic_parsed = apply_dynamic_readability(scraper)

  good_dynamic = scraper._isReaderable()

  parsed_markdown = dynamic_parsed if (good_dynamic and dynamic_parsed) else static_parsed

  scraper.close_driver()

  return parsed_markdown

if __name__ == "__main__":
    import getopt
    opts, args = getopt.getopt(sys.argv[1:], 'd')
    for (k, v) in opts:
       if k == "-d": debug_mode = True

    markdown_content = scrape(args[0])
    print(markdown_content)
