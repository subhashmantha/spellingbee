from bs4 import BeautifulSoup
import requests

import re
# as per recommendation from @freylis, compile once only
CLEANR = re.compile('<.*?>')

def cleanhtml(raw_html):
  cleantext = re.sub(CLEANR, '', raw_html)
  return cleantext

inlinks = open('wiki_urls.csv',encoding="utf-8")
# url='https://en.wikipedia.org/wiki/Lists_of_English_words_by_country_or_language_of_origin'
w=inlinks.readlines()
for x in w:
    filenam = x.split('|')[0].replace('/','_')+'.txt'
    url=url='https://en.wikipedia.org'+x.split('|')[0]
    try:
        html_content = requests.get(url).text
        soup = BeautifulSoup(html_content, "lxml")
        file2 = open('{}.txt'.format(filenam.replace(' ','_')),'a',encoding="utf-8")
        for x in soup.find_all('li'):
            n = cleanhtml(x.__str__()).replace('\n',' ')
            file2.write(n+'\n')
    except:
        print('abc')
    file2.close()
inlinks.close()








