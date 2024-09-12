import urllib.request, re #import needed modules for python3
# letters="abcdefghijklmnopqrstuvwxyz0"
letters='eghijklmnopqrstuvwxyz0'
url="http://"+ "www" + "." + "merriam-webster" + ".com"
url2="/browse/dictionary/"
word_list=[]
import codecs
for letter in letters:
    newurl=url+url2+letter
    file_open = codecs.open('mw_all_words_{}_.csv'.format(letter), 'w+', "utf-8-sig")
    print(newurl)
    text=urllib.request.urlopen(newurl).read().decode('utf-8') #open the url, read it and change the encoding to utf-8. Needed to use regex on it
    regex="("+url2+ letter + "/" +"[0-9]+)"
    liste=re.findall(regex, text) #regex finds all occurences of the specific
    # liste = liste[0:10]
    for link in liste:
        newurl2=url+link
        text2=urllib.request.urlopen(newurl2).read().decode('utf-8')
        # print(text2)
        regex2='href="/dictionary/.+">(.+)</a>'
        liste2=re.findall(regex2, text2)
        # print(liste2[0:100])
        # liste3 = liste2[0:100]
        for word in liste2:
            word = word.replace('<span>','')
            word = word.replace('</span>', '')
            url3="http://"+ "www" + "." + "merriam-webster" + ".com/dictionary/" #link
            url4=url3+word #concatenate url and word to form the final url
            word2 = word+"\n"
            print(word2)
            file_open.write(word2)
            file_open.flush()
            # print(url4)
            try:
                text3=urllib.request.urlopen(url4).read().decode('latin-1', errors='ignore') #open the url, read it and change the encoding to utf-8. Needed to use regex on it
                # print(url4)
                # class ="parts-of-speech"
                # "contentURL": "https://media.merriam-webster.com/audio/prons/en/us/mp3

                tup= (word,
                                  url4,
                                  '|'.join(re.findall('<p class="et">\n(.+)</p>',text3,re.MULTILINE)),
                                  '|'.join(re.findall('"og:description" content="(.+)See the full definition" />', text3)),
                                  '|'.join(re.findall('"parts-of-speech"><a class="important-blue-link" href="/dictionary/(.+)">(.+)</a>', text3)),
                                  '|'.join(re.findall(f"https://media.merriam-webster.com/audio/prons/en/us/mp3/{letter}/(.+)", text3))) #regex finds all occurences of the specific
                # print(tup)
                # # write_str = '=~='.join(tup)+'\n'
                # print(write_str)

            except:
                continue
    file_open.close()