
# coding: utf-8

# In[ ]:




# In[1]:

# urlquery from Achim Tack. Thank you!
# https://github.com/ATack/GoogleTrafficParser/blob/master/google_traffic_parser.py
def urlquery(url):
    # function cycles randomly through different user agents and time intervals to simulate more natural queries
    try:
        import urllib2
        import random
        from random import choice
        import time

        sleeptime = float(random.randint(1,6))/5
        time.sleep(sleeptime)

        agents = ['Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1309.0 Safari/537.17',
        'Mozilla/5.0 (compatible; MSIE 10.6; Windows NT 6.1; Trident/5.0; InfoPath.2; SLCC1; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET CLR 2.0.50727) 3gpp-gba UNTRUSTED/1.0',
        'Opera/12.80 (Windows NT 5.1; U; en) Presto/2.10.289 Version/12.02',
        'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)',
        'Mozilla/3.0',
        'Mozilla/5.0 (iPhone; U; CPU like Mac OS X; en) AppleWebKit/420+ (KHTML, like Gecko) Version/3.0 Mobile/1A543a Safari/419.3',
        'Mozilla/5.0 (Linux; U; Android 0.5; en-us) AppleWebKit/522+ (KHTML, like Gecko) Safari/419.3',
        'Opera/9.00 (Windows NT 5.1; U; en)']

        agent = choice(agents)
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', agent)]
        #print agent

        html = opener.open(url).read()
        time.sleep(sleeptime)
        
        return html

    except:
        print "fehler in urlquery"


# In[2]:

def immoscout24parser(url):
    try:
        from bs4 import BeautifulSoup
        import json

        soup = BeautifulSoup(urlquery(url), 'html.parser')

        scripts = soup.findAll('script')
        for script in scripts:
            if script.text.strip().startswith('var IS24 = IS24'):
                s = script.string.split('\r\n')


        for line in s:
            if line.strip().startswith('model'):
                immo_json = line.strip()
                immo_json = json.loads(immo_json[7:-1])
            if line.strip().startswith('numberOfPages'):
                maxpages = int(line.split()[1])
                #print maxpages
            if line.strip().startswith('currentPageIndex'):
                page = int(line.split()[1].strip(','))
                #print page

        return [immo_json, page, maxpages]
    
    except Exception, e:
        print "fehler in immoscout24 parser: %s" % e


# In[3]:




# In[4]:

immos = {}

kind = ['Wohnung', 'Haus']
what = ['Miete', 'Kauf']

for k in kind:
    for w in what:
        
        page = 0
        print('Suche %s / %s' % (k, w))
        
        while True:
            page+=1
            url = 'http://www.immobilienscout24.de/Suche/S-T/P-%s/%s-%s/Sachsen/Dresden?pagerReporting=true' % (page, k, w)

            # Because of some timeout or immoscout24.de errors,
            # we try until it works \o/
            immo_json = None
            while immo_json is None:
                try:
                    immo_json, actualpage, maxpages = immoscout24parser(url)
                except:
                    pass

            if page>maxpages:
                break

            # Get the data
            for rj in immo_json['results']:
                immo = {}

                immo_id = rj['id']

                immo[u'Adresse'] = rj['address']
                immo[u'Stadt'] = rj['city']
                immo[u'Titel'] = rj['title']
                immo[u'PLZ'] = rj['zip']
                immo[u'Stadtteil'] = rj['district']
                immo[u'Features'] = rj['checkedAttributes']
                immo[u'Grundriss'] = rj['hasFloorplan']
                immo[u'von privat'] = rj['privateOffer']

                for i in range(len(rj['attributes'])):
                    immo[rj['attributes'][i]['title']] = rj['attributes'][i]['value']

                immo[u'Miete/Kauf'] = w
                immo[u'Haus/Wohnung'] = k
                
                try:
                    immo[u'From'] = rj['contactName']
                except:
                    immo[u'From'] = None

                try:
                    immo[u'Bilder'] = rj['mediaCount']
                except:
                    immo[u'Bilder'] = 0

                try:
                    immo[u'Lat'] = rj['latitude']
                    immo[u'Lon'] = rj['longitude']
                except:
                    immo[u'Lat'] = None
                    immo[u'Lon'] = None

                immos[immo_id] = immo

            print('Scrape Page %i/%i (%i Immobilien %s %s gefunden)' % (actualpage, maxpages, len(immos), k, w))


# In[5]:

import datetime
timestamp = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d-%H-%M')


# In[ ]:




# In[6]:

import pandas as pd


# In[73]:

df = pd.DataFrame(immos).T
df.index.name = 'ID'


# In[74]:

len(df)


# In[81]:

df[(df['Haus/Wohnung']=='Wohnung') & (df['Miete/Kauf']=='Kauf')].head()


# In[83]:

import uuid
def anoymousfrom(name):
    try:
        return str(uuid.uuid3(uuid.NAMESPACE_DNS, name.encode('utf-8')))
    except:
        return 'NaN'


# In[84]:

df['From_UUID'] = df['From'].apply(anoymousfrom)


# In[85]:

exportcols = [col for col in df.columns if col not in ['From']]


# In[87]:

df.to_csv('%s-immo-komplett.csv' % timestamp, columns=exportcols, encoding='utf-8')
for k in kind:
    for w in what:
        print('Speichere %s / %s' % (k, w))
        f = open('%s-%s-%s.csv' % (timestamp, k, w), 'w')
        f.write('# %s %s from immoscout24.de on %s\n' % (k,w,timestamp))
        df[(df['Haus/Wohnung']==k) & (df['Miete/Kauf']==w)].to_csv(f, columns=exportcols, encoding='utf-8')
        f.close()


# In[ ]:



