
# coding: utf-8

# In[1]:

import pandas as pd
import numpy as np
import json

get_ipython().magic(u'matplotlib inline')
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_context('talk')


# ## Stadtteile Dresden

# In[112]:

with open('./stadtteile-Dresden.json') as data_file:    
    stadtteil_json = json.load(data_file)


# In[113]:

stadtteile_osm = []
for i, stadtteil in enumerate(stadtteil_json['features']):
    try:
        stadtteilname = stadtteil['properties']['name']
        stadtteile_osm.append(stadtteilname)
    except:
        continue
        
stadtteile_osm.sort()


# In[114]:

stadtteile_osm


# ## Postleitzahlen Dresden

# In[5]:

plzs = "01057,01067,01069,01097,01099,01108,01109,01127,01129,01139,01156,01157,01159,01169,01187,01189,01217,01219,01227,01237,01239,01257,01259,01277,01279,01307,01309,01312,01324,01326,01327,01328,01329,01462,01465,01728"


# In[6]:

ddplzs = plzs.split(',')


# ### QGIS Filter output

# In[7]:

for plz in ddplzs:
    print('"plz" LIKE "%s" OR' % plz.strip())


# ## Daten lesen

# In[8]:

data = pd.read_csv('2015-08-09-17-49-immo-komplett.csv', encoding='utf-8', dtype={'PLZ': str})


# In[9]:

data.index = data.ID


# In[10]:

data.head()


# ## Daten Cleanen

# ### Preise cleanen

# In[11]:

def preiscleaner(preis, mio=False):
    #print preis
    try:
        p = preis.split()
        p = float(p[0].replace('.', '').replace(',','.'))
        if mio:
            return p/1e6
        else:
            return int(p)
    except:
        return preis


# In[12]:

data['Kaufpreis'] = data['Kaufpreis'].apply(preiscleaner, mio=True)
data['Kaltmiete'] = data['Kaltmiete'].apply(preiscleaner)


# In[ ]:




# ### Flächen cleanen

# In[13]:

def squaremetercleaner(squaremeter):
    #print squaremeter
    try:
        m = squaremeter.split()
        m = float(m[0].replace(',', '.'))
        return int(m)
    except:
        return 0.0    


# In[14]:

data[u'Wohnfläche'] = data[u'Wohnfläche'].apply(squaremetercleaner)


# ### Zimmeranzahl

# In[15]:

data[u'Zimmer'] = data[u'Zimmer'].str.replace(',','.').astype('float')


# In[16]:

data.head()


# ## Verkaufsvolumen

# In[17]:

verkaufgroup = data[data['Miete/Kauf']=='Kauf'].groupby('From').sum()


# In[18]:

verkaufgroup.sort('Kaufpreis', ascending=True, inplace=True)
verkaufgroup['Kaufpreis'].dropna(inplace=True)


# In[19]:

verkaufgroup['Kaufpreis'].tail(10)


# In[20]:

verkaufgroup['Kaufpreis'][-10:].plot(kind='barh', title='Volumen Kauf-Immobilien in Dresden, Gruppiert nach Anbieter')

plt.xlabel(u'mio €')
plt.tight_layout()
plt.savefig('Groupby-Anbieter-KaufpreisSumme.png', dpi=150)


# ## Anzahl an Immobilien

# In[21]:

fromgroup = data.groupby(['From','Miete/Kauf']).count()


# In[22]:

fromgroup.sort('ID', ascending=True, inplace=True)


# In[23]:

fromgroup['ID'][-10:].plot(kind='barh', title='Angebotene Immobilien in Dresden, Gruppiert nach Anbieter')

plt.xlabel('Anzahl')
plt.tight_layout()
plt.savefig('Groupby-Anbieter.png', dpi=150)


# # Immopreis Predictor

# In[24]:

from sklearn.metrics import r2_score
from sklearn import linear_model
from sklearn.tree import DecisionTreeRegressor
from sklearn import preprocessing


# 

# In[25]:

mietwohnungen = data[(data['Miete/Kauf']=='Miete') & (data['Haus/Wohnung']=='Wohnung')]
kaufwohnungen = data[(data['Miete/Kauf']=='Kauf') & (data['Haus/Wohnung']=='Wohnung')]


# Kaltmieten über 5000€ sind unrealistisch und sind Fehler bei Eingabe auf immoscout24.de (Kauf statt Miete), die werfen wir raus.

# In[26]:

mietwohnungen = mietwohnungen[mietwohnungen.Kaltmiete < 5000.0]


# ## Verkaufspreis schätzen

# In[ ]:




# In[27]:

X = pd.concat([kaufwohnungen[[u'Wohnfläche', u'Zimmer']], pd.get_dummies(kaufwohnungen[u'Stadtteil'])], axis=1)
y = kaufwohnungen['Kaufpreis']


# In[28]:

# Robustly fit linear model with RANSAC algorithm
regressor = linear_model.RANSACRegressor(linear_model.LinearRegression())


# In[29]:

regressor.fit(X,y)


# In[30]:

inlier_mask = regressor.inlier_mask_
outlier_mask = np.logical_not(inlier_mask)
print(u'%.1f%% der Wohnungen als Ausreißer identifiziert' % (sum(outlier_mask)*100.0/(sum(outlier_mask)+sum(inlier_mask))))


# In[31]:

y_pred = regressor.predict(X)
kaufwohnungen[u'Kaufpreis (geschätzt)'] = y_pred


# In[32]:

r2_ransac = r2_score(y[inlier_mask], y_pred[inlier_mask])


# In[33]:

sns.regplot(kaufwohnungen['Kaufpreis'][inlier_mask],
            kaufwohnungen[u'Kaufpreis (geschätzt)'][inlier_mask])
plt.scatter(kaufwohnungen['Kaufpreis'][outlier_mask],
            kaufwohnungen[u'Kaufpreis (geschätzt)'][outlier_mask],
            alpha=0.4,
            c='r')

plt.title(u'Schätzung des Kaufpreises (in mio €) von Eigentumswohnungen in Dresden\n(Stadtteil, Anzahl Zimmer, Wohnfläche)')
plt.text(0.85, 0.95, r'$R^2=%.2f$' % r2_ransac)
plt.xlim(0, 1.1)
plt.ylim(0, 1.1)
plt.tight_layout()
plt.savefig('LinReg-Kauf-Wohnung.png', dpi=150)


# In[34]:

X.columns[2:]


# In[70]:

len(stadtteile)


# In[115]:

# Immoscout Datensatz durch gehen und schauen,
# ob die Stadtteile auch den Namen der offiziellen
# Stadtteile tragen
for stadtteil in X.columns[2:]:
    # Da bei einigen nur der Beginn der Namen gleich ist,
    # müssen wir leider alle durch gehen :)
    
    
    
    print(u'✓ %s' % (stadtteil))     


# In[ ]:




# In[ ]:




# In[ ]:




# In[246]:

X.columns


# In[248]:

sum(X[u'Äußere Neustadt (Antonstadt)'])


# In[249]:

X_my = np.zeros(103)
X_my[0] = 121.0
X_my[1] = 3.0
X_my[-1] = 1


# In[250]:

y_my = regressor.predict(X_my)[0][0]


# In[185]:

print('Geschätzter Marktwert: %.3f€' % (1000.0*y_my))


# ## Kaltmiete schätzen
# 
# ### Nur mit Wohnfläche und Anzahl der Zimmer

# In[37]:

X = mietwohnungen[[u'Wohnfläche', u'Zimmer']]
y = mietwohnungen['Kaltmiete']


# In[38]:

reg = linear_model.LinearRegression()


# In[39]:

reg.fit(X, y)


# In[40]:

y_pred = reg.predict(X)


# In[41]:

mietwohnungen[u'Kaltmiete geschätzt'] = y_pred


# In[42]:

r_2 = r2_score(y, y_pred)


# In[43]:

sns.regplot(mietwohnungen['Kaltmiete'] ,mietwohnungen[u'Kaltmiete geschätzt'])
plt.title(u'Schätzung der Kaltmiete von Mietwohnungen in Dresden\n(Anzahl Zimmer, Fläche)')
plt.text(2600, 2100, r'$R^2=%.2f$' % r_2)
plt.xlim(0, 3000)
plt.ylim(0, 3000)


# ### Vorhersage

# In[44]:

m = 155 # m2
z = 4  # Zimmer
print('Kaltmiete für %iR-Wohnung %im^2 in Dresden: %i€' % (z, m, reg.predict([m, z])))


# In[45]:

for z in range(2, 6):
    for m in range(40, 200, 10):
        print('Kaltmiete für %iR-Wohnung %im^2 in Dresden: %i€' % (z, m, reg.predict([m, z])))


# ### Zusätzlich noch Lage (Postleitzahl)

# In[46]:

X2 = pd.concat([X, pd.get_dummies(mietwohnungen[u'PLZ'])], axis=1)


# In[47]:

reg2 = linear_model.LinearRegression()


# In[48]:

reg2.fit(X2, y)


# In[49]:

y2_pred = reg2.predict(X2)


# In[50]:

mietwohnungen[u'Kaltmiete geschätzt (mit Lage)'] = y2_pred


# In[51]:

r_22 = r2_score(y, y2_pred)


# In[52]:

sns.regplot(mietwohnungen['Kaltmiete'] ,mietwohnungen[u'Kaltmiete geschätzt (mit Lage)'])
plt.title(u'Schätzung der Kaltmiete von Mietwohnungen in Dresden\n(Lage, Anzahl Zimmer, Fläche)')
plt.text(2600, 2100, r'$R^2=%.2f$' % r_22)
plt.xlim(0, 3000)
plt.ylim(0, 3000)


# ## Outlier detection

# In[53]:

# Robustly fit linear model with RANSAC algorithm
model_ransac = linear_model.RANSACRegressor(linear_model.LinearRegression(), residual_threshold=250.0)


# In[54]:

model_ransac.fit(X2, y)


# In[55]:

inlier_mask = model_ransac.inlier_mask_
outlier_mask = np.logical_not(inlier_mask)
print(u'%.1f%% der Wohnungen als Ausreißer identifiziert' % (sum(outlier_mask)*100.0/(sum(outlier_mask)+sum(inlier_mask))))


# In[56]:

y2_pred_ransac = model_ransac.predict(X2)


# In[57]:

mietwohnungen[u'Kaltmiete geschätzt (mit Lage)'] = y2_pred_ransac.astype('int')


# In[58]:

r_22_ransac = r2_score(y[inlier_mask], y2_pred_ransac[inlier_mask])


# In[59]:

sns.regplot(mietwohnungen['Kaltmiete'][inlier_mask],
            mietwohnungen[u'Kaltmiete geschätzt (mit Lage)'][inlier_mask])
plt.scatter(mietwohnungen['Kaltmiete'][outlier_mask],
            mietwohnungen[u'Kaltmiete geschätzt (mit Lage)'][outlier_mask],
            alpha=0.1,
            c='r')

plt.title(u'Schätzung der Kaltmiete von Mietwohnungen in Dresden\n(Lage, Anzahl Zimmer, Fläche)')
plt.text(2600, 2100, r'$R^2=%.2f$' % r_22_ransac)
plt.xlim(0, 3000)
plt.ylim(0, 3000)
plt.tight_layout()
plt.savefig('LinReg.png', dpi=150)


# ## Vorhersage für alle Postleitzahlen

# ### Datencheck: Sind alle PLZ vorhanden?

# In[60]:

len(X2.columns[2:]) == len(ddplzs)


# In[61]:

for plz in X2.columns[2:]:
    if plz in ddplzs:
        print(u'%s ✓' % plz)
    else:
        print(u'%s ✗' % plz)


# In[62]:

X2.head(1)


# ### Prediction

# In[98]:

for raum in range(2, 6):
    kaltmietenDD = pd.DataFrame()
    A = pd.Series(raum*25.0 * np.ones(len(ddplzs)))
    Z = pd.Series(raum * np.ones(len(ddplzs)))

    X_pred = pd.concat([A, Z, pd.get_dummies(ddplzs)], axis=1)

    kaltmieten = model_ransac.predict(X_pred)

    kaltmietenDD = pd.DataFrame(data={'Wohnfläche': A, 'Zimmer': Z, 'PLZ': ddplzs, 'Kaltmiete': kaltmieten.flatten()})

    kaltmietenDD['KaltmieteProQm'] = kaltmietenDD['Kaltmiete'] / kaltmietenDD['Wohnfläche']

    kaltmietenDD[['PLZ', 'KaltmieteProQm']].to_csv('Kaltmieten%sR.csv' % raum, index=False, float_format='%.2f')


# In[99]:

kaltmietenDD.head()


# ## Top 10 günstige Wohnungen finden

# In[71]:

mietwohnungen[u'Differenz zur Schätzung'] = mietwohnungen[u'Kaltmiete'] - mietwohnungen[u'Kaltmiete geschätzt (mit Lage)']


# In[72]:

topmietwohnungen = mietwohnungen.sort(u'Differenz zur Schätzung')


# ### 3 Raum

# In[73]:

topmietwohnungen[topmietwohnungen['Zimmer']==3][['Titel', u'Wohnfläche', 'Kaltmiete', u'Differenz zur Schätzung', 'Stadtteil', 'Zimmer']].head(10)


# ### 4 Raum

# In[74]:

topmietwohnungen[topmietwohnungen['Zimmer']==4][['Titel', u'Wohnfläche', 'Kaltmiete', u'Differenz zur Schätzung', 'Stadtteil', 'Zimmer']].head(10)


# ### 5 Raum

# In[75]:

topmietwohnungen[topmietwohnungen['Zimmer']==5][['Titel', u'Wohnfläche', 'Kaltmiete', u'Differenz zur Schätzung', 'Stadtteil', 'Zimmer']].head(10)


# Fragen? @Balzer82

# In[ ]:




# In[ ]:




# In[ ]:



