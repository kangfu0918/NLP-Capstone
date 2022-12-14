# -*- coding: utf-8 -*-
"""Sentiment Analysis Gnews automation Stock Return.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/11SLiPQT5eQ2Km27OQVeID2ue4xs35f7r
"""

# Google news api library install
!pip install gnews

# Import required library
from gnews import GNews
import pandas as pd
import datetime
import nltk
nltk.download('vader_lexicon')
from nltk.sentiment.vader import SentimentIntensityAnalyzer
sid = SentimentIntensityAnalyzer()
import re
import string
import unicodedata
!pip install unidecode
import unidecode
!pip install yfinance
import yfinance as yf
import scipy.stats as stats

# Define a function called get_news to pull news from googlenews
def get_news(Language='en',Country='US', Company='Microsoft'): 
# Google news setting
    google_news = GNews(language=Language, country=Country)
    news = google_news.get_news(Company)
    news_title=[]
    news_text=[]
    news_date=[]
    news_author=[]
    for i in range(len(news)):
        article = google_news.get_full_article(
        news[i]['url'])
        if article != None: 
            news_title.append(article.title)
            news_text.append(article.text)
            news_author.append(article.authors)
            news_date.append(news[i]['published date'])
    news_df=pd.DataFrame(list(zip(news_title,news_date,news_author,news_text)),columns=['title','publish date', 'author','text'])
    news_df['datetime']=news_df['publish date'].apply(lambda x: datetime.datetime.strptime(x, '%a, %d %b %Y %H:%M:%S %Z'))
    news_df=news_df.drop(columns=['publish date'])
    news_df['date']=news_df['datetime'].apply(lambda x: x.date())
    news_df=news_df.sort_values('date', ascending=False)
    return news_df

# Define a function called get_sentiment_score to score the polarity of news
def get_sentiment_score(news_df):
    def preprocess(text):
        text=text.lower()
        text=re.sub(r'[^\w\s]', '', text)
        text=unidecode.unidecode(text)
        text=re.sub(r'\d+', '', text)
        return text
    news_df['text']=news_df['text'].apply(lambda x: preprocess(x))
    news_df['polarity scores']=news_df['text'].apply(lambda x: sid.polarity_scores(x))
    news_df['compound scores']=news_df['polarity scores'].apply(lambda x: x['compound'])
    news_df_grouped=news_df.groupby('date')
    mean_df=news_df_grouped.mean()
    mean_df=mean_df.reset_index()
    return mean_df

# Define a function called get_stock to get stock price from Yahoo Finance
def get_stock(stocks=['MSFT'],start_date = '2022-05-01',stop_date = '2022-06-30'):
    stock_list = " ".join(stocks)
    table = yf.download(stock_list, start=start_date, end=stop_date)['Adj Close']
    df_stock=pd.DataFrame(table)
    df_stock=df_stock.reset_index().rename(columns={'Adj Close':'Close Price'})
    df_stock['date']=df_stock['Date'].apply(lambda x:x.date())
    df_stock=df_stock.drop(columns=['Date'])
    return df_stock

# Define a function called get_correlation_coefficient to investigate the relationship between the sentiment scores of news and stock return
# stock return = ((P1-P0)+D1)/P0 where D1=0
def get_correlation_coefficient(mean_df,df_stock):
    df_final=pd.merge(mean_df,df_stock,how='left',on='date').dropna()
    df_final['Close Price Last Day']=df_final['Close Price'].shift(1)
    df_final['Stock Return']=(df_final['Close Price']-df_final['Close Price Last Day'])/df_final['Close Price Last Day']
    df_final=df_final.dropna()
    r = stats.pearsonr(df_final['compound scores'], df_final['Stock Return'])
    print("Pearson Correlation coefficient:"+str(r[0]))
    return r[0]

# Define a function to get correlation coefficient between news' sentiment score and stock price of companies
def corr_coefficient(company, ticker):
    news_df=get_news(Company=company)
    sentiment_df=get_sentiment_score(news_df)
    start_d=sentiment_df['date'][0]
    end_d=sentiment_df['date'][len(sentiment_df)-1]
    stock_df=get_stock(stocks=ticker,start_date=start_d,stop_date=end_d)
    r=get_correlation_coefficient(sentiment_df,stock_df)
    return r

# Define a function called corr_df to automate the whole sentiment analysis process
def corr_df(companylist,tickers):
  corr_list=[]
  for i in range(len(companylist)):
      corr_list.append(corr_coefficient(companylist[i],[tickers[i]]))
  corr_df=pd.DataFrame(list(zip(companylist,corr_list)),columns=['company','corr_value'])
  return corr_df

# 11 companies sample 
df1=corr_df(['RBC','Microsoft','Amazon','CVR Energy','OXY','Coinbase','IBM','Alpha Metallurgical','Peabody Energy','AAPL','Consol Energy'],['RY','MSFT','AMZN','CVI','OXY','COIN','IBM','AMR','BTU','AAPL','CEIX'])

# Display correlation coefficient dataframe df1
df1

# ETF sentiment analysis
# 5 interested ETF
df2=corr_df(['iShares US Healthcare','iShares US Consumer Goods','iShares S&P 500 Growth','ARKK','ARKW'],['IYH','IYK','IVW','ARKK','ARKW'])

# Display correlation coefficient dataframe of ETF df2
df2