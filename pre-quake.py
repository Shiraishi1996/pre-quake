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
import plotly.express as px
from streamlit_folium import st_folium
import folium  

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
print(dfjapan)
dfjapan["geoCode"] = dfjapan["geoCode"].str.replace("JP-","").astype(int)
dfjapan["lat"] = [43.06417,40.82444,39.70361,38.26889,39.71861,38.24056,37.75,36.34139,36.56583,36.39111,35.85694,35.60472,35.68944,35.44778,37.90222,36.69528,36.59444,36.06528,35.66389,36.65139,35.39111,34.97694,35.18028,34.73028,35.00444,35.02139,34.68639,34.69139,34.68528,34.22611,35.50361,35.47222,34.66167,34.39639,34.18583,34.06583,34.34028,33.84167,33.55972,33.60639,33.24944,32.74472,32.78972,33.23806,31.91111,31.56028,26.2125]
dfjapan["lon"] = [141.34694,140.74,141.1525,140.87194,140.1025,
140.36333	,
140.46778	,
140.44667	,
139.88361	,
139.06083	,
139.64889	,
140.12333	,
139.69167	,
139.6425	,
139.02361	,
137.21139	,
136.62556	,
136.22194	,
138.56833	,
138.18111	,
136.72222	,
138.38306	,
136.90667	,
136.50861	,
135.86833	,
135.75556	,
135.52	,
135.18306	,
135.83278	,
135.1675	,
134.23833	,
133.05056	,
133.935	,
132.45944	,
131.47139	,
134.55944	,
134.04333	,
132.76611	,
133.53111	,
130.41806	,
130.29889	,
129.87361	,
130.74167	,
131.6125	,
131.42389	,
130.55806	,
127.68111	,
]


# 地図の中心の緯度/経度、タイル、初期のズームサイズを指定します。
m = folium.Map(
    # 地図の中心位置の指定(今回は栃木県の県庁所在地を指定)
    location=[36.56583, 139.88361], 
    # タイル、アトリビュートの指定
    tiles='https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png',
    attr='都道府県庁所在地、人口、面積(2016年)',
    # ズームを指定
    zoom_start=6
)

# 読み込んだデータ(緯度・経度、ポップアップ用文字、アイコンを表示)
for i, row in dfjapan.iterrows():
    # ポップアップの作成(都道府県名＋都道府県庁所在地＋人口＋面積)
    pop=str(search_keyword)
    folium.Marker(
        # 緯度と経度を指定
        location=[row['lat'], row['lon']],
        # ツールチップの指定(都道府県名)
        tooltip=row['geoCode'],
        # ポップアップの指定
        popup=folium.Popup(pop, max_width=300),
        # アイコンの指定(アイコン、色)
        icon=folium.Icon(icon="home",icon_color="white", color="red")
    ).add_to(m)

st_data = st_folium(m, width=1200, height=800)

cmap = plt.get_cmap('Reds')
norm = plt.Normalize(vmin=dfjapan[search_keyword].min(), vmax=dfjapan[search_keyword].max())
fcol = lambda x: '#' + bytes(cmap(norm(x), bytes=True)[:3]).hex()

fig, ax = plt.subplots(1,1, figsize=(10,10))
plt.colorbar(plt.cm.ScalarMappable(norm, cmap))
plt.imshow(picture(dfjapan[search_keyword].apply(fcol)))
print(picture(dfjapan[search_keyword].apply(fcol)))
st.write("Googleにおける検索キーワードの都道府県毎の注目度")
st.pyplot(fig)

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
