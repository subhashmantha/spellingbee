from bs4 import BeautifulSoup
import requests

import re
# as per recommendation from @freylis, compile once only
CLEANR = re.compile('<.*?>')

def cleanhtml(raw_html):
  cleantext = re.sub(CLEANR, '', raw_html)
  return cleantext
url='https://en.wikipedia.org/wiki/English_words_of_African_origin'
# url='https://www.translationdirectory.com/glossaries/glossary209.php'
html_content = requests.get(url).text
soup = BeautifulSoup(html_content, "lxml")

# file1 = open('all_links.txt','a',encoding="utf-8")
file2 = open('Wiki_English_words_of_African_origin.txt','a',encoding="utf-8")
for x in soup.find_all('li'):
    # print(x)
    # file2.write(n+'\n')
    # w1 = x.find_all('ul')
    n = cleanhtml(x.__str__()).replace('\n', ' ')
    file2.write(n+'\n')
    # if n.find('-') > -1:
    #     w=x.find_all('a')
    #     # print(w)
    #     for f in w:
    #
    #         s=f.get("href")
    #         title = f.get("title")
    #         print(s,"|",title,"|",n)

# file1.close()
# file2.close()
#
#






