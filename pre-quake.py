import streamlit as st
import requests
import bs4
import pandas as pd
import pandas as pd
import snscrape.modules.twitter as sntwitter
import itertools
import codecs
from pytrends.request import TrendReq
from japanmap import picture
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import datetime 

dt_today = datetime.date.today()
dt_minus = datetime.timedelta(days = 10)
dt_week = dt_today - dt_minus

@st.cache
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode("utf-8-sig")

st.title('検索ワードの注目度解析')

search_keyword = st.text_input('検索ワード', '今日の地震')
st.write('検索ワード', search_keyword)

# googleに接続
pytrend = TrendReq(hl='ja-jp',tz=540)

# キーワードの設定　5キーワード以上は内部エラーになる
kw_list = [search_keyword]
# googleにリクエストする。
pytrend.build_payload(kw_list=kw_list, timeframe= str(dt_week)+" "+str(dt_today), geo="JP")
# 小区域別のインタレストの取得
st.dataframe(pytrend.interest_over_time())

#st.dataframe(pytrend.interest_by_region(resolution='COUNTRY',
#                            inc_geo_code=True).sort_values('geoCode'))

dfjapan = pytrend.interest_by_region(resolution="JP", inc_low_vol=True, inc_geo_code=True)
dfjapan["geoCode"] = dfjapan["geoCode"].str.replace("JP-","").astype(int)

cmap = plt.get_cmap('Reds')
norm = plt.Normalize(vmin=dfjapan[search_keyword].min(), vmax=dfjapan[search_keyword].max())
fcol = lambda x: '#' + bytes(cmap(norm(x), bytes=True)[:3]).hex()

#ax, fig = plt.subplots(figsize=(10,10))
#plt.colorbar(plt.cm.ScalarMappable(norm, cmap))

#plt.imshow(picture(dfjapan[search_keyword].apply(fcol)))
#st.pyplot(fig)

st.write('【検索した単語】{}'.format(search_keyword))
#検索順位取得処理
#Google検索の実施
search_url = 'https://www.google.co.jp/search?hl=ja&num=10&q=' + search_keyword
res_google = requests.get(search_url)
#Responseオブジェクトが持つステータスコードが200番台(成功)以外だったら、エラーメッセージを吐き出してスクリプトを停止します。
res_google.raise_for_status()
st.write("Google検索結果を取得")

#res_google.textは、検索結果のページのHTML
bs4_google = bs4.BeautifulSoup(res_google.text, 'lxml')
google_search_page = bs4_google.select('div.kCrYT>a')

#rank:検索順位
rank = 1
site_rank = []
site_title = []
site_url = []

for site in google_search_page:
    try:    
        site_title.append(site.select('h3.zBAuLc')[0].text)
        site_url.append(site.get('href').split('&sa=U&')[0].replace('/url?q=', ''))
        site_rank.append(rank)
        rank +=1
    except IndexError:
        continue


df = pd.DataFrame({'順位':site_rank, 'タイトル':site_title, 'URL':site_url})

@st.cache
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode("utf-8-sig")

st.dataframe(df) 

csv = convert_df(df)

st.download_button(
    label="Download data as CSV",
    data=csv,
    file_name='Google_search.csv',
    mime='text/csv',
)

st.write("Twitter検索結果を取得")

#twitterでスクレイピングを行い特定キーワードの情報を取得
scraped_tweets = sntwitter.TwitterSearchScraper(search_keyword).get_items()

#最初の10ツイートだけを取得し格納
sliced_scraped_tweets = itertools.islice(scraped_tweets, 10)

#データフレームに変換する
df2 = pd.DataFrame(sliced_scraped_tweets)

st.dataframe(df2) 

csv2 = convert_df(df2)

st.download_button(
    label="Download data as CSV",
    data=csv2,
    file_name='Twitter_analysis.csv',
    mime='text/csv',
)

