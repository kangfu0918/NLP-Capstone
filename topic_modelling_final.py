# -*- coding: utf-8 -*-
"""Topic Modelling_ RBC GAM.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1-tKztXPO99FqnVCGFicggJRu3tPPo8GI

# Web Scrapping

Rapid API provides API to get articles from Seeking Alpha 

API call to get ETF articles from Seeking Alpha is derived this link
https://rapidapi.com/apidojo/api/seeking-alpha

This program produces a csv file that has market outlook summary from seeking alpha for August 6, 2022

API allows us only to get only 40 articles
"""

# Get access to Seeking Alpha
import requests

url = "https://seeking-alpha.p.rapidapi.com/articles/v2/list"

querystring = {"until":"0","since":"0","size":"40","number":"1","category":"market-outlook"}

headers = {
	"X-RapidAPI-Key": "039012b65dmsh8fab3e6eb98e2cbp182020jsn3b6d41df7915",
	"X-RapidAPI-Host": "seeking-alpha.p.rapidapi.com"
}
# Load articles

response = requests.request("GET", url, headers=headers, params=querystring)

print(response.text)

import json
json_data = json.loads(response.text)

print(json_data["data"])

data_links = json_data["data"]

for links in data_links:
  print(links["links"]["self"])

# Build a aricles sumamry Dataframe of Load articles
import re

data_links = json_data["data"]
result_set = []

for links in data_links:
  link = links["links"]["self"]
  url = "https://seekingalpha.com" + link
  response = requests.request("GET", url)
  extracted=str(re.findall(r'"summary"\:\[.*"lastModified"',response.text)[0])
  replaced=extracted.replace("\"summary\":[","").replace("\"lastModified\"","")
  extract_words=re.sub('[^A-Za-z0-9 .]+', '', replaced)
  result_set.append(extract_words)

# Show the article sumamry dataframe
from os import truncate
import pandas as pd

df=pd.DataFrame({'data': result_set})
#pd.set_option('display.max_colwidth', None)
display(df)

# Save the summary dataframe to csv file
df.to_csv("dataset.csv")

"""# Topic Modelling

Import Data
"""

import pandas as pd

df = pd.read_csv("dataset.csv")['data']

"""Split imported data into train and test"""

train = df[0:35]
test = df[36:]

"""Convert train dataframe to list"""

train_list = train.values.tolist()

train_list

"""Convert test dataframe to list"""

test_list = test.values.tolist()

test_list

# Imports
import gensim
import gensim.corpora as corpora
from gensim import models

import matplotlib.pyplot as plt
import matplotlib.pyplot as plt

import spacy

from pprint import pprint

import en_core_web_sm
nlp = en_core_web_sm.load()
nlp.max_length = 1500000

"""Pre processing steps

1.Remove white space from front and end of each document

2.Remove new line characters

3.Remove carriage returns

4.Remove extra spaces

5.Used 'spacy' library to parse each document and get only  nouns, adjectives and verbs and discard others.

6.Apply lemmatization to the above result set
"""

# To store pre processed documents
document_list = []
words_list = []

for doc in train_list:
  
    # Pre processing
    doc = doc.strip()  # Remove white space from start and end
    doc = doc.replace('\n', ' ') # Remove new line
    doc = doc.replace('\r', '') # Remove carriage return
    while '  ' in doc:
        doc = doc.replace('  ', ' ') # Remove extra spaces
    
    # Parse document with SpaCy
    parsed = nlp(doc)
    
    tmp_doc = [] # Temporary list to store individual document
    
    # Further cleaning and selection of text characteristics
    for token in parsed:
        # Retain only Noun , adjective and verb
        if token.is_stop == False and token.is_punct == False and (token.pos_ == "NOUN" or token.pos_ == "ADJ" or token.pos_ =="VERB"): 
            # Apply lemmatization
            tmp_doc.append(token.lemma_.lower()) # Convert to lower case and retain the lemmatized version of the word (this is a string object)
            words_list.append(token.lemma_.lower())
    document_list.append(tmp_doc) # Build the training corpus 'list of lists'

"""Top 10 frequently used words in the training set"""

df_words = pd.DataFrame(words_list, columns =['words'])

dfg = df_words.groupby('words').words.count() \
                               .reset_index(name='count') \
                               .sort_values(['count'], ascending=False) \
                               .head(10).reset_index(drop=True)

dfg.plot.bar(x='words')

"""We used genesim library to perform LDA. LDA requires 3 important parameters

1. Pre processed training Set 
2. Number of topics
3. Each document converted into bag of words

Since the dataset is limited , we set the number of topics to 3 . 

"""

ID2word = corpora.Dictionary(document_list)

# Apply bag of words to the training documents
train_corpus = [ID2word.doc2bow(doc) for doc in document_list]

# Set number of topics to 3. This can be increased if we had a larger dataset
num_of_topics = 3 

# Train LDA model on the training corpus
lda_model = gensim.models.LdaMulticore(corpus=train_corpus, 
                                       num_topics=num_of_topics, 
                                       id2word=ID2word, 
                                       passes=100,
                                       random_state = 72)

"""Key words from each of the 3 topics"""

pprint(lda_model.print_topics(num_words=4))

"""Model Evalutaion:

  We used topic coherence as a metric for our model evaluation. Topic coherence is a way to measure sematic similarity between topic scoring words in a topic

 By using bag of words , we got a score of 0.3763067825710997. 
"""

# Find Coherence

# Coherence model
coherence_model_lda = gensim.models.CoherenceModel(model=lda_model, 
                                                   texts=document_list,
                                                   dictionary=ID2word, 
                                                   coherence='c_v')

# Find Coherence
coherence_lda = coherence_model_lda.get_coherence()

print('Coherence Score:', coherence_lda)

"""As an opportunity to improve the score , we added TF IDF to the bag of words"""

# Set up Bag of Words and TFIDF
corpus = [ID2word.doc2bow(doc) for doc in document_list]

# Fit TF-IDF model
TFIDF = models.TfidfModel(corpus) 

# Apply TF-IDF model
trans_TFIDF = TFIDF[corpus]

lda_model = gensim.models.LdaMulticore(corpus= trans_TFIDF,
                                       num_topics=num_of_topics,
                                       id2word=ID2word, 
                                       passes=100,
                                       random_state = 72)

pprint(lda_model.print_topics(num_words=4))

"""Got an improved coherence score after implementing TF IDF"""

# Find Coherence score

# Coherence model
coherence_model_lda = gensim.models.CoherenceModel(model=lda_model, texts=document_list, dictionary=ID2word, coherence='c_v')

# Find coherence
coherence_lda = coherence_model_lda.get_coherence()

print('Coherence Score:', coherence_lda)

"""Following gives topic probability distribution of each document. 

For example , Document 1 has 0.8863 probablity that it belongs to topic 0 , 0.0550104 probablity that it belongs to topic 1 and 0.0586895 probability that it belongs to topic 2
"""

doc_no = 0 # Set document counter
for doc in document_list:
    TFIDF_doc = TFIDF[corpus[doc_no]] # Apply TFIDF model to individual documents
    print(lda_model.get_document_topics(TFIDF_doc)) # Get and print document topic allocations
    doc_no += 1

df_density_dist = pd.DataFrame()

"""Word frequency distribution for topic 1"""

df_words = pd.DataFrame(lda_model.show_topic(0, topn=30), columns =['words', 'frequencies'])

df_words.plot.bar(x='words')

"""We now move on to label each of the topics

Highest density for topic 0 is observed from Row 1 which is 0.88

Corresponding document below:

"*Global government bond yields ended the month lower in July as fears of an economic downturn have pushed some investors back into the sovereign debt market.For policymakers reigning in rising inflation continues to be topofmind and central banks globally are hiking interest rates as they try to slowdown the economy and curb increasing prices.The Japanese 10year government bond ended the month with a closing yield of 0.17 an almost 5 basis point drop from the month prior.*"

As observed from frequency distribution and from the above document, we can make an intuitive conclusion that topic 0 is about recession . Hence we can label topic 0 as **"Recession"**


"""

df_words = pd.DataFrame(lda_model.show_topic(1, topn=30), columns =['words', 'frequencies'])

df_words.plot.bar(x='words')

"""Highest density for topic 1 is observed from Row 7 which is 0.89

Corresponding document below

"*High frequency indicators can give us a nearly uptothemoment view of the economy.The metrics are divided into long leading short leading and coincident indicators.The long and shortterm forecasts remain negative and the nowcast is neutral.But there have been several important improvements as interest rates in e.g. mortgages have declined significantly in the last month and gas prices are close to back below 4u002Fgallon.*"

As observed from the above document, we can make an intuitive conclusion that topic 1 is about market forecasts . Hence we can label topic 1 as **"Market forecasts"** . Topic 1 was not strong enough to give us a good label. If we had a larger dataset, we would have obtained a better label


"""

df_words = pd.DataFrame(lda_model.show_topic(2, topn=30), columns =['words', 'frequencies'])

df_words.plot.bar(x='words')

"""For topic 2, lets pick up row 22 which has a  topic 2 density of 0.88

Corresponding document below:

"*The Armageddon scenario for corporate earnings has not materialized adding stability to the equity market.Global economic data continues to disappoint. The UK is now forecasting a long recession.The Geopolitical tensions of today can morph into severe ramifications for the US economy tomorrow.Tax and Spend is the continuing theme but it wont help a weakening economy saddled with inflation.*"

As observed from frequency distribution and from the above document, we can make an intuitive conclusion that topic 2 is also about recession . Hence we can label topic 3 as **"Recession"**

We make a strong conclusion that "Recession" is the market outlook

Now moving on to validation,
"""

# Test with trained model above. Repeat the steps from training phase

test_set = test.values.tolist()

new_documents = [] 

for doc in test_set:
    
    # Pre processed
    doc = doc.strip()  # Remove white space at the beginning and end
    doc = doc.replace('\n', ' ') # Replace the \n (new line) character with space
    doc = doc.replace('\r', '') # Replace the \r (carriage returns -if you're on windows) with null
    while '  ' in doc:
        doc = doc.replace('  ', ' ') # Remove extra spaces
    
    # Parse document with SpaCy
    parsed = nlp(doc)
    
    tmp_doc = [] # Temporary list to store individual document
    
    # Further cleaning and selection of text characteristics
    for token in parsed:
       # Retain only Noun , adjective and verb
        if token.is_stop == False and token.is_punct == False and (token.pos_ == "NOUN" or token.pos_ == "ADJ" or token.pos_ =="VERB"): # Retain words that are not a stop word nor punctuation, and only if a Noun, Adjective or Verb
        # Apply lemmatization
            tmp_doc.append(token.lemma_.lower()) 
    new_documents.append(tmp_doc)

NewDocumentTopix = [] # For plotting the new document topics

doc_no = 0 # Set document counter
for doc in new_documents:
    new_corpus = [ID2word.doc2bow(doc) for doc in new_documents] # Apply Bag of Words to new documents
    new_TFIDF = models.TfidfModel(new_corpus) # Fit TF-IDF model
    TFIDF_doc = TFIDF[new_corpus[doc_no]] # Apply TFIDF model
    NewDocumentTopix.append(lda_model.get_document_topics(TFIDF_doc)) # Get the new document topic allocations and store for plotting
    print(NewDocumentTopix[doc_no]) # Print new document topic allocations
    doc_no += 1

"""Topic 2 from third row above has the highest density. We had labelled topic 2 as "Recession". 

Row 3 from test set mentions about recession. Hence it makes an intuitive sense

"In 2017 and 2018 CBRT repatriated all its gold from the Federal Reserve Bank of New York and the Bank for International Settlements and all but 6 tonnes from BOE.Yet in 2020 and 2021 CBRT began shipping gold back from Turkey to London and at the end of 2021 it was holding 78 tonnes at the BOE. Amid **economic turmoil** thats weakening the Turkish lira CBRT is likely using its gold at BOE as collateral for FX loans.Computing Turkeys net gold reserves is complicated because since 2011 CBRT and the Turkish Treasury have launched several schemes to borrow gold which all show up on the central banks balance *italicized text* sheet."

Though the results from the above excercise might not be accurate, this approach can be applied to large datasets to observe better results.
"""