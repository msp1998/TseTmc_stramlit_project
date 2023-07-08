import streamlit as st
import pandas as pd
import plotly
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()
import aiohttp
import asyncio
from unsync import unsync
import tracemalloc
import datetime
import jdatetime
import persiantools
import time

from persiantools import characters
from IPython.display import clear_output

def link_debth_and_market_price(xx=10):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    for _ in range(xx):
        try :
            r = requests.get('http://old.tsetmc.com/tsev2/data/MarketWatchPlus.aspx', headers=headers)
        except:
            continue
        time.sleep(.5)
        if len(r.text)>100:
            break
    
    return(r.text)

def green_highlight(val):
    color = '#90EE90' if val else 'white'
    return f'background-color: {color}'

def red_highlight(val):
    color = '#FFCCCB' if val else 'white'
    return f'background-color: {color}'

def sector_name():
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    r = requests.get('http://old.tsetmc.com/Loader.aspx?ParTree=111C1213', headers=headers)
    sectro_lookup = (pd.read_html(r.text)[0]).iloc[1:,:]
    # convert from Arabic to Farsi and remove half-space
    sectro_lookup[1] = sectro_lookup[1].apply(lambda x: (str(x).replace('ي','ی')).replace('ك','ک'))
    sectro_lookup[1] = sectro_lookup[1].apply(lambda x: x.replace('\u200c',' '))
    sectro_lookup[1] = sectro_lookup[1].apply(lambda x: x.strip())
    return(dict(sectro_lookup[[0, 1]].values))

def market_in_time(link,sector_pd , mode=1):
    main_text = link
    Mkt_df = pd.DataFrame((main_text.split('@')[2]).split(';'))
    Mkt_df = Mkt_df[0].str.split(",",expand=True)
    Mkt_df = Mkt_df.iloc[:,:23]
    Mkt_df.columns = ['WEB-ID','Ticker-Code','Ticker','Name','Time','Open','Final','Close','No','Volume','Value',
                      'Low','High','Y_Final','EPS','Base-Vol','Unknown1','Unknown2','sector_name','Day_UL','Day_LL','Share-No','Mkt-ID']
    # re-arrange columns and drop some columns:
    Mkt_df = Mkt_df[['WEB-ID','Ticker','Name','Time','Open','Final','Close','No','Volume','Value',
                      'Low','High','Y_Final','EPS','Base-Vol','sector_name','Day_UL','Day_LL','Share-No','Mkt-ID']]
    # Just keep: 300 Bourse, 303 Fara-Bourse, 305 Sandoogh, 309 Payeh, 400 H-Bourse, 403 H-FaraBourse, 404 H-Payeh
    Mkt_ID_list = ['300','303','305','309','400','403','404']
    Mkt_df = Mkt_df[Mkt_df['Mkt-ID'].isin(Mkt_ID_list)]
    Mkt_df['Market'] = Mkt_df['Mkt-ID'].map({'300':'بورس','303':'فرابورس','305':'صندوق قابل معامله','309':'پایه','400':'حق تقدم بورس','403':'حق تقدم فرابورس','404':'حق تقدم پایه'})
    Mkt_df.drop(columns=['Mkt-ID'],inplace=True)   # we do not need Mkt-ID column anymore
    Mkt_df['sector_name'] = Mkt_df['sector_name'].map(sector_pd)
    Mkt_df['Ticker'] = Mkt_df['Ticker'].apply(lambda x: persiantools.characters.ar_to_fa(x))
    Mkt_df['Name'] = Mkt_df ['Name'].apply(lambda x: persiantools.characters.ar_to_fa(x))
    Mkt_df['Name'] = Mkt_df['Name'].apply(lambda x: (str(x).replace('آ','ا')))
    Mkt_df['Ticker'] = Mkt_df['Ticker'].apply(lambda x: persiantools.characters.ar_to_fa(x))
    Mkt_df['Ticker'] = Mkt_df['Ticker'].apply(lambda x: (str(x).replace('آ','ا')))
    Mkt_df['Ticker'] = Mkt_df['Ticker'].apply(lambda x: (str(x).replace('ي','ی')))
    Mkt_df['Ticker'] = Mkt_df['Ticker'].apply(lambda x: (str(x).replace('ك','ک')))
    Mkt_df['Ticker'] = Mkt_df['Ticker'].apply(lambda x: (str(x).replace(' ','')))
    cols = ['Open','Final','Close','Volume','Value', 'Low','High','Y_Final','Base-Vol','Day_UL','Day_LL','Share-No']
    Mkt_df[cols] = Mkt_df[cols].astype("float")
    Mkt_df['Close(%)'] = round((Mkt_df['Close']-Mkt_df['Y_Final'])/Mkt_df['Y_Final']*100,2)
    Mkt_df['Final(%)'] = round((Mkt_df['Final']-Mkt_df['Y_Final'])/Mkt_df['Y_Final']*100,2)
    Mkt_df['Market Cap'] = round(Mkt_df['Share-No']*Mkt_df['Final'],2)
    # set index
    Mkt_df['WEB-ID'] = Mkt_df['WEB-ID'].apply(lambda x: x.strip())
    if mode == 1:
        return(Mkt_df)
    elif mode == 2:
        dele = Mkt_df[(Mkt_df.Ticker.str.contains('2')) | (Mkt_df.Ticker.str.contains('4'))].index
        Mkt_df = Mkt_df.drop(dele)
        return(Mkt_df)

def debth_market(link):
   
    main_text = link
    
    market_info = pd.read_excel(r'stocks_id_info.xlsx')
    OB_df = pd.DataFrame((main_text.split('@')[3]).split(';'))
    
    OB_df = OB_df[0].str.split(",",expand=True)
    OB_df.columns = ['WEB-ID','OB-Depth','S_N','B_N','B_P','S_P','B_V','S_V']
    OB_df = OB_df[['WEB-ID','OB-Depth','S_N','S_V','S_P','B_P','B_V','B_N']]
    OB_df = OB_df.sort_values(by=['WEB-ID','OB-Depth'])
    OB_df['WEB-ID'] = OB_df['WEB-ID'].apply(lambda x: x.strip())
    OB_df = OB_df.reset_index(drop=True).astype('int64')
    OB_df = OB_df.merge(market_info,on='WEB-ID')

    OB_df['sector_name'] = OB_df['sector_name'].apply(lambda x: (str(x).replace('ي','ی')).replace('ك','ک'))
    OB_df['sector_name'] = OB_df['sector_name'].apply(lambda x: x.replace('\u200c',' '))
    OB_df['sector_name'] = OB_df['sector_name'].apply(lambda x: x.strip())
    OB_df['sector_name'] = OB_df['sector_name'].apply(lambda x: persiantools.characters.ar_to_fa(x))
    OB_df['Ticker'] = OB_df['Ticker'].apply(lambda x: persiantools.characters.ar_to_fa(x))
    OB_df['Ticker'] = OB_df['Ticker'].apply(lambda x: (str(x).replace('آ','ا')))
    OB_df['Ticker'] = OB_df['Ticker'].apply(lambda x: (str(x).replace('ي','ی')))
    OB_df['Ticker'] = OB_df['Ticker'].apply(lambda x: (str(x).replace('ك','ک')))
    OB_df['Ticker'] = OB_df['Ticker'].apply(lambda x: (str(x).replace(' ','')))
    
    return(OB_df)

def need_of_total_info():
    r = requests.get('http://old.tsetmc.com/tsev2/data/ClientTypeAll.aspx')
    Mkt_RI_df = pd.DataFrame(r.text.split(';'))
    Mkt_RI_df = Mkt_RI_df[0].str.split(",",expand=True)
    # assign names to columns:
    Mkt_RI_df.columns = ['WEB-ID','No_Buy_R','No_Buy_I','Vol_Buy_R','Vol_Buy_I','No_Sell_R','No_Sell_I','Vol_Sell_R','Vol_Sell_I']
    # convert columns to numeric type:
    cols = ['No_Buy_R','No_Buy_I','Vol_Buy_R','Vol_Buy_I','No_Sell_R','No_Sell_I','Vol_Sell_R','Vol_Sell_I']
    Mkt_RI_df[cols] = Mkt_RI_df[cols].apply(pd.to_numeric, axis=1)
    Mkt_RI_df['WEB-ID'] = Mkt_RI_df['WEB-ID'].apply(lambda x: x.strip())
    Mkt_RI_df = Mkt_RI_df.set_index('WEB-ID')
    # re-arrange the order of columns:
    Mkt_RI_df = Mkt_RI_df[['No_Buy_R','No_Buy_I','No_Sell_R','No_Sell_I','Vol_Buy_R','Vol_Buy_I','Vol_Sell_R','Vol_Sell_I']]
    return(Mkt_RI_df)

def total_info(link1 , market_sector_pd_for_map , need_):
    
    OB_df = pd.DataFrame((link1.split('@')[3]).split(';'))
    OB_df = OB_df[0].str.split(",",expand=True)
    OB_df.columns = ['WEB-ID','OB-Depth','S_N','B_N','B_P','S_P','B_V','S_V']
    OB_df = OB_df[['WEB-ID','OB-Depth','S_N','S_V','S_P','B_P','B_V','B_N']]
    
    OB1_df = (OB_df[OB_df['OB-Depth']=='1']).copy()         # just keep top row of OB
    OB1_df.drop(columns=['OB-Depth'],inplace=True)
    OB1_df['WEB-ID'] = OB1_df['WEB-ID'].apply(lambda x: x.strip())
    OB1_df = OB1_df.set_index('WEB-ID')
    cols = ['S_N','S_V','S_P','B_P','B_V','B_N']
    OB1_df[cols] = OB1_df[cols].apply(pd.to_numeric, axis=1)
    Mkt_df = market_in_time(link1 , market_sector_pd_for_map)
    Mkt_df = Mkt_df.set_index('WEB-ID')
    Mkt_df = Mkt_df.join(OB1_df)
    bq_value = Mkt_df.apply(lambda x: int(x['B_V']*x['B_P']) if(x['B_P']==x['Day_UL']) else 0 ,axis = 1)
    sq_value = Mkt_df.apply(lambda x: int(x['S_V']*x['S_P']) if(x['S_P']==x['Day_LL']) else 0 ,axis = 1)
    Mkt_df = pd.concat([Mkt_df,pd.DataFrame(bq_value,columns=['BQ-Value']),pd.DataFrame(sq_value,columns=['SQ-Value'])],axis=1)
    # calculate buy/sell queue average per-capita:
    bq_pc_avg = Mkt_df.apply(lambda x: int(round(x['BQ-Value']/x['B_N'],0)) if((x['BQ-Value']!=0) and (x['B_N']!=0)) else 0 ,axis = 1)
    sq_pc_avg = Mkt_df.apply(lambda x: int(round(x['SQ-Value']/x['S_N'],0)) if((x['SQ-Value']!=0) and (x['S_N']!=0)) else 0 ,axis = 1)
    Mkt_df = pd.concat([Mkt_df,pd.DataFrame(bq_pc_avg,columns=['BQPC']),pd.DataFrame(sq_pc_avg,columns=['SQPC'])],axis=1)
    final_df = Mkt_df.join(need_)
    final_df['Trade Type'] = pd.DataFrame(final_df['Ticker'].apply(lambda x: 'تابلو' if((not x[-1].isdigit())or(x in ['انرژی1','انرژی2','انرژی3'])) 
                                                                   else ('بلوکی' if(x[-1]=='2') else ('عمده' if(x[-1]=='4') else ('جبرانی' if(x[-1]=='3') else 'تابلو')))))
    jdatetime_download = jdatetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S")
    final_df['Download'] = jdatetime_download
    # just keep necessary columns and re-arrange theor order:
    final_df = final_df[['Ticker','Trade Type','Time','Open','High','Low','Close','Final','Close(%)','Final(%)',
                         'Day_UL', 'Day_LL','Value','BQ-Value', 'SQ-Value', 'BQPC', 'SQPC',
                         'Volume','Vol_Buy_R', 'Vol_Buy_I', 'Vol_Sell_R', 'Vol_Sell_I','No','No_Buy_R', 'No_Buy_I', 'No_Sell_R', 'No_Sell_I',
                         'Name','Market','sector_name','Share-No','Base-Vol','Market Cap','EPS','Download']]
    final_df = final_df.reset_index()
    final_df['Ticker'] = final_df['Ticker'].apply(lambda x : characters.ar_to_fa(''.join(x.split('\u200c')).strip()))
    final_OB_df = ((Mkt_df[['Ticker','Day_LL','Day_UL']]).join(OB_df.set_index('WEB-ID')))
    # convert columns to numeric int64
    cols = ['Day_LL','Day_UL','OB-Depth','S_N','S_V','S_P','B_P','B_V','B_N']
    final_OB_df[cols] = final_OB_df[cols].astype('int64')
    # sort using tickers and order book depth:
    final_OB_df = final_OB_df.sort_values(['Ticker','OB-Depth'], ascending = (True, True))
    final_OB_df = final_OB_df.set_index(['Ticker','Day_LL','Day_UL','OB-Depth'])
    return final_df.drop('WEB-ID', axis=1)

def plot_buy_sell_RI(data):
    df = pd.DataFrame((data[['Val_Buy_R', 'Val_Buy_I', 'Val_Sell_R', 'Val_Sell_I']].sum()/(data['Value'].sum()/10**12)), columns=['% of buy'])
    #colors
    colors = ['green','orange','red','orange']
    fig, (ax1, ax2) = plt.subplots(1, 2)
    ax1.pie(df['% of buy'].iloc[:2], colors = colors[:2], labels=df.index[:2], autopct='%1.1f%%', startangle=90)
    ax2.pie(df['% of buy'].iloc[2:], colors = colors[2:], labels=df.index[2:], autopct='%1.1f%%', startangle=90)
    #draw circle
    # Equal aspect ratio ensures that pie is drawn as a circle
    ax1.axis('equal') 
    ax2.axis('equal')  
    plt.tight_layout()
    return fig

def add_column(data):
    ##add values column
    data['Val_Buy_R'] = data['Vol_Buy_R'] * data['Final']/10**10
    data['Val_Sell_R'] = data['Vol_Sell_R'] * data['Final']/10**10
    data['Val_Buy_I'] = data['Vol_Buy_I'] * data['Final']/10**10
    data['Val_Sell_I'] = data['Vol_Sell_I'] * data['Final']/10**10
    #add power columns
    data['Power_Buy_R'] = data['Val_Buy_R'] / data['No_Buy_R']
    data['Power_Sell_R'] = data['Val_Sell_R'] / data['No_Sell_R']
    data['Balance_R'] = (data['Val_Buy_R'] - data['Val_Sell_R'])
    return data

def get_fix_stock_etfs(x):
    types = ['صندوق سهامی', 'صندوق درآمد ثابت', 'سایر صندوق‌ها']
    if '-س' in x:
        return types[0]
    elif 'سهام' in x:
        return types[0]
    elif 'شاخص' in x:
        return types[0]
    elif '-د' in x:
        return types[1]
    elif 'ثابت' in x:
        return types[1]
    elif 'پایدار' in x:
        return types[1]
    else:
        return types[2]

def get_time():
    time = jdatetime.datetime.now()
    time = str(time.year) + '-' + str(time.month) + '-'  + str(time.day) + ', ' + str(time.hour) + ':' + str(time.minute)
    return time

st. set_page_config(layout="wide")


market_info = pd.read_excel(r'stocks_id_info.xlsx')
market_sector_pd_for_map = sector_name()

st.sidebar.title('بورس یا اختیار یا آتی')
market_choice = st.sidebar.radio('choose what you want',['بورس','اختیار' , 'آتی'])
bourse_choices = st.sidebar.radio('more specifics',['عمق بازار','اطلاعات کلی' , '....'])
time.sleep(5)

stock_or_sector = st.sidebar.radio('more and more specifics',['پرتفوی 6 تایی','بر اساس صنعت'])

time.sleep(5)

just1 = link_debth_and_market_price() 
just1 = debth_market(just1)
need__ = need_of_total_info()

bourse_sector = st.sidebar.selectbox('sectors :',just1.sector_name.unique())

d_stock = st.multiselect('select your stocks (pick 6 of them):',just1.Ticker.unique() ,key = 'six_stock')

placeholder = st.empty()
placeholder2 = st.empty()

#st.sidebar.write(list(just1.sector_name.unique()))
#req = link_debth_and_market_price()
#market_price = market_in_time(req , market_sector_pd_for_map,2)
#x = market_price[market_price.Ticker == 'وسپه']
#xx = just1[just1.Ticker == 'وسپه']
#st.dataframe(just1[just1.Ticker == 'بهير'])
#st.dataframe(market_price)
#x1 ,x2 =st.columns(2)
#with x1:
#    st.write(market_price[market_price['sector_name'].str.contains("سرمایه گذاریها")].Ticker.unique())
#with x2:
#    st.write(just1[just1.sector_name.str.contains("سرمایه گذاریها")].Ticker.unique())
#.sector_name.str.contains("سرمایه گذاریها")
                
 
for seconds in range(500):
    req = link_debth_and_market_price(5)
    if market_choice=='بورس':
        debth = debth_market(req)
        market_price = market_in_time(req , market_sector_pd_for_map,2)
        if (bourse_choices== 'عمق بازار') and (stock_or_sector == 'بر اساس صنعت'):     

            debth = debth.drop('WEB-ID',axis=1)
            with placeholder.container():
                if bourse_sector=="بانکها و موسسات اعتباری":
                    debth = debth[debth.sector_name.str.contains("بانکها و موسسات اعتباری")]
                    names = debth.Ticker.unique()
                    counter=0
                    st.subheader("**last update: {}**".format(get_time()))
                    for i_ in range(int(len(names)/3)):      
                        bank1, bank2, bank3 = st.columns([1,1,1],gap='small')
                        F = market_price[market_price.Ticker == (names[counter])]
                        F1 = market_price[market_price.Ticker == (names[counter+1])]
                        F2 = market_price[market_price.Ticker == (names[counter+2])]
                        with bank1:
                            st.write(names[counter] +f'F  : {int(F.Final)}  ...  {round((int(F.Final)/int(F.Y_Final)-1)*100,2)}    _and_  Last : {int(F.Close)}  ...  {round((int(F.Close)/int(F.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter]].drop(['flow','Ticker','OB-Depth','sector_name'],axis = 1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width=True
                                        )
                        with bank2:
                            st.write(names[counter+1] +f'  F  : {int(F1.Final)}  ...  {round((int(F1.Final)/int(F1.Y_Final)-1)*100,2)}  _and_  Last : {int(F1.Close)} ... {round((int(F1.Close)/int(F1.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+1]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width=True
                                        )   
                        with bank3:
                            st.write(names[counter+2] +f'   F  : {int(F2.Final)}  ...  {round((int(F2.Final)/int(F2.Y_Final)-1)*100,2)}  _and_  Last : {int(F2.Close)}  ...  {round((int(F2.Close)/int(F2.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker== names[counter+2]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width = True
                                        )
                        counter +=3
                
                elif bourse_sector=="سرمایه گذاریها":
                    debth = debth[debth.sector_name.str.contains("سرمایه گذاریها")]
                    names = debth.Ticker.unique()
                    counter=0
                    st.subheader("**last update: {}**".format(get_time()))
                    for i_ in range(int(len(names)/3)):      
                        bank1, bank2, bank3 = st.columns([1,1,1],gap='small')
                        F = market_price[market_price.Ticker == names[counter]]
                        F1 = market_price[market_price.Ticker == names[counter+1]]
                        F2 = market_price[market_price.Ticker == names[counter+2]]
                        with bank1:
                            st.write(names[counter] +f'F  : {int(F.Final)}  ...  {round((int(F.Final)/int(F.Y_Final)-1)*100,2)}    _and_  Last : {int(F.Close)}  ...  {round((int(F.Close)/int(F.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter]].drop(['flow','Ticker','OB-Depth','sector_name'],axis = 1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width=True
                                        )
                        with bank2:
                            st.write(names[counter+1] +f'  F  : {int(F1.Final)}  ...  {round((int(F1.Final)/int(F1.Y_Final)-1)*100,2)}  _and_  Last : {int(F1.Close)} ... {round((int(F1.Close)/int(F1.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+1]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width=True
                                        )   
                        with bank3:
                            st.write(names[counter+2] +f'   F  : {int(F2.Final)}  ...  {round((int(F2.Final)/int(F2.Y_Final)-1)*100,2)}  _and_  Last : {int(F2.Close)}  ...  {round((int(F2.Close)/int(F2.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+2]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width = True
                                        )
                        counter +=3
                    
                elif bourse_sector=="هتل و رستوران":
                    debth = debth[debth.sector_name.str.contains("هتل و رستوران")]
                    names = debth.Ticker.unique()
                    counter=0
                    st.subheader("**last update: {}**".format(get_time()))
                    for i_ in range(int(len(names)/3)):      
                        bank1, bank2, bank3 = st.columns([1,1,1],gap='small')
                        F = market_price[market_price.Ticker == (names[counter])]
                        F1 = market_price[market_price.Ticker == (names[counter+1])]
                        F2 = market_price[market_price.Ticker == (names[counter+2])]
                        with bank1:
                            st.write(names[counter] +f'F  : {int(F.Final)}  ...  {round((int(F.Final)/int(F.Y_Final)-1)*100,2)}    _and_  Last : {int(F.Close)}  ...  {round((int(F.Close)/int(F.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter]].drop(['flow','Ticker','OB-Depth','sector_name'],axis = 1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width=True
                                        )
                        with bank2:
                            st.write(names[counter+1] +f'  F  : {int(F1.Final)}  ...  {round((int(F1.Final)/int(F1.Y_Final)-1)*100,2)}  _and_  Last : {int(F1.Close)} ... {round((int(F1.Close)/int(F1.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+1]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width=True
                                        )   
                        with bank3:
                            st.write(names[counter+2] +f'   F  : {int(F2.Final)}  ...  {round((int(F2.Final)/int(F2.Y_Final)-1)*100,2)}  _and_  Last : {int(F2.Close)}  ...  {round((int(F2.Close)/int(F2.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+2]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width = True
                                        )
                        counter +=3

                elif bourse_sector=="لاستیک و پلاستیک":
                    debth = debth[debth.sector_name.str.contains("لاستیک و پلاستیک")]
                    names = debth.Ticker.unique()
                    counter=0
                    st.subheader("**last update: {}**".format(get_time()))
                    for i_ in range(int(len(names)/3)):      
                        bank1, bank2, bank3 = st.columns([1,1,1],gap='small')
                        F = market_price[market_price.Ticker == (names[counter])]
                        F1 = market_price[market_price.Ticker == (names[counter+1])]
                        F2 = market_price[market_price.Ticker == (names[counter+2])]
                        with bank1:
                            st.write(names[counter] +f'F  : {int(F.Final)}  ...  {round((int(F.Final)/int(F.Y_Final)-1)*100,2)}    _and_  Last : {int(F.Close)}  ...  {round((int(F.Close)/int(F.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter]].drop(['flow','Ticker','OB-Depth','sector_name'],axis = 1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width=True
                                        )
                        with bank2:
                            st.write(names[counter+1] +f'  F  : {int(F1.Final)}  ...  {round((int(F1.Final)/int(F1.Y_Final)-1)*100,2)}  _and_  Last : {int(F1.Close)} ... {round((int(F1.Close)/int(F1.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+1]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width=True
                                        )   
                        with bank3:
                            st.write(names[counter+2] +f'   F  : {int(F2.Final)}  ...  {round((int(F2.Final)/int(F2.Y_Final)-1)*100,2)}  _and_  Last : {int(F2.Close)}  ...  {round((int(F2.Close)/int(F2.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+2]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width = True
                                        )
                        counter +=3

                elif bourse_sector=="سیمان، آهک و گچ":
                    debth = debth[debth.sector_name.str.contains("سیمان، آهک و گچ")]
                    names = debth.Ticker.unique()
                    counter=0
                    
                    st.subheader("**last update: {}**".format(get_time()))
                    for i_ in range(int(len(names)/3)):      
                        bank1, bank2, bank3 = st.columns([1,1,1],gap='small')
                        F = market_price[market_price.Ticker == (names[counter])]
                        F1 = market_price[market_price.Ticker == (names[counter+1])]
                        F2 = market_price[market_price.Ticker == (names[counter+2])]
                        with bank1:
                            st.write(names[counter] +f'F  : {int(F.Final)}  ...  {round((int(F.Final)/int(F.Y_Final)-1)*100,2)}    _and_  Last : {int(F.Close)}  ...  {round((int(F.Close)/int(F.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter]].drop(['flow','Ticker','OB-Depth','sector_name'],axis = 1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width=True
                                        )
                        with bank2:
                            st.write(names[counter+1] +f'  F  : {int(F1.Final)}  ...  {round((int(F1.Final)/int(F1.Y_Final)-1)*100,2)}  _and_  Last : {int(F1.Close)} ... {round((int(F1.Close)/int(F1.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+1]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width=True
                                        )   
                        with bank3:
                            st.write(names[counter+2] +f'   F  : {int(F2.Final)}  ...  {round((int(F2.Final)/int(F2.Y_Final)-1)*100,2)}  _and_  Last : {int(F2.Close)}  ...  {round((int(F2.Close)/int(F2.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+2]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width = True
                                        )
                        counter +=3
                                    
                elif bourse_sector=="محصولات شیمیایی":
                    debth = debth[debth.sector_name.str.contains("محصولات شیمیایی")]
                    names = debth.Ticker.unique()
                    counter=0
                    st.subheader("**last update: {}**".format(get_time()))
                    for i_ in range(int(len(names)/3)):      
                        bank1, bank2, bank3 = st.columns([1,1,1],gap='small')
                        F = market_price[market_price.Ticker == (names[counter])]
                        F1 = market_price[market_price.Ticker == (names[counter+1])]
                        F2 = market_price[market_price.Ticker == (names[counter+2])]
                        with bank1:
                            st.write(names[counter] +f'F  : {int(F.Final)}  ...  {round((int(F.Final)/int(F.Y_Final)-1)*100,2)}    _and_  Last : {int(F.Close)}  ...  {round((int(F.Close)/int(F.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter]].drop(['flow','Ticker','OB-Depth','sector_name'],axis = 1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width=True
                                        )
                        with bank2:
                            st.write(names[counter+1] +f'  F  : {int(F1.Final)}  ...  {round((int(F1.Final)/int(F1.Y_Final)-1)*100,2)}  _and_  Last : {int(F1.Close)} ... {round((int(F1.Close)/int(F1.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+1]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width=True
                                        )   
                        with bank3:
                            st.write(names[counter+2] +f'   F  : {int(F2.Final)}  ...  {round((int(F2.Final)/int(F2.Y_Final)-1)*100,2)}  _and_  Last : {int(F2.Close)}  ...  {round((int(F2.Close)/int(F2.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+2]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width = True
                                        )
                        counter +=3

                elif bourse_sector=="فعالیتهای کمکی به نهادهای مالی واسط":
                    debth = debth[debth.sector_name.str.contains("فعالیتهای کمکی به نهادهای مالی واسط")]
                    names = debth.Ticker.unique()
                    counter=0
                    
                    st.subheader("**last update: {}**".format(get_time()))
                    for i_ in range(int(len(names)/3)):      
                        bank1, bank2, bank3 = st.columns([1,1,1],gap='small')
                        
                        F = market_price[market_price.Ticker == (names[counter])]
                        F1 = market_price[market_price.Ticker == (names[counter+1])]
                        F2 = market_price[market_price.Ticker == (names[counter+2])]
                        with bank1:
                            st.write(names[counter] +f'F  : {int(F.Final)}  ...  {round((int(F.Final)/int(F.Y_Final)-1)*100,2)}    _and_  Last : {int(F.Close)}  ...  {round((int(F.Close)/int(F.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter]].drop(['flow','Ticker','OB-Depth','sector_name'],axis = 1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width=True
                                        )
                        with bank2:
                            st.write(names[counter+1] +f'  F  : {int(F1.Final)}  ...  {round((int(F1.Final)/int(F1.Y_Final)-1)*100,2)}  _and_  Last : {int(F1.Close)} ... {round((int(F1.Close)/int(F1.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+1]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width=True
                                        )   
                        with bank3:
                            st.write(names[counter+2] +f'   F  : {int(F2.Final)}  ...  {round((int(F2.Final)/int(F2.Y_Final)-1)*100,2)}  _and_  Last : {int(F2.Close)}  ...  {round((int(F2.Close)/int(F2.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+2]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width = True
                                        )
                        counter +=3

                elif bourse_sector=="سایر واسطه گریهای مالی":
                    debth = debth[debth.sector_name.str.contains("سایر واسطه گریهای مالی")]
                    names = debth.Ticker.unique()
                    counter=0
                    st.subheader("**last update: {}**".format(get_time()))
                    for i_ in range(int(len(names)/3)):      
                        bank1, bank2, bank3 = st.columns([1,1,1],gap='small')
                        
                        F = market_price[market_price.Ticker == (names[counter])]
                        F1 = market_price[market_price.Ticker == (names[counter+1])]
                        F2 = market_price[market_price.Ticker == (names[counter+2])]
                        with bank1:
                            st.write(names[counter] +f'F  : {int(F.Final)}  ...  {round((int(F.Final)/int(F.Y_Final)-1)*100,2)}    _and_  Last : {int(F.Close)}  ...  {round((int(F.Close)/int(F.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter]].drop(['flow','Ticker','OB-Depth','sector_name'],axis = 1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width=True
                                        )
                        with bank2:
                            st.write(names[counter+1] +f'  F  : {int(F1.Final)}  ...  {round((int(F1.Final)/int(F1.Y_Final)-1)*100,2)}  _and_  Last : {int(F1.Close)} ... {round((int(F1.Close)/int(F1.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+1]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width=True
                                        )   
                        with bank3:
                            st.write(names[counter+2] +f'   F  : {int(F2.Final)}  ...  {round((int(F2.Final)/int(F2.Y_Final)-1)*100,2)}  _and_  Last : {int(F2.Close)}  ...  {round((int(F2.Close)/int(F2.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+2]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width = True
                                        )
                        counter +=3

                elif bourse_sector=="مواد و محصولات دارویی":
                    debth = debth[debth.sector_name.str.contains("مواد و محصولات دارویی")]
                    names = debth.Ticker.unique()
                    counter=0
                    st.subheader("**last update: {}**".format(get_time()))
                    for i_ in range(int(len(names)/3)):      
                        bank1, bank2, bank3 = st.columns([1,1,1],gap='small')
                        
                        F = market_price[market_price.Ticker == (names[counter])]
                        F1 = market_price[market_price.Ticker == (names[counter+1])]
                        F2 = market_price[market_price.Ticker == (names[counter+2])]
                        with bank1:
                            st.write(names[counter] +f'F  : {int(F.Final)}  ...  {round((int(F.Final)/int(F.Y_Final)-1)*100,2)}    _and_  Last : {int(F.Close)}  ...  {round((int(F.Close)/int(F.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter]].drop(['flow','Ticker','OB-Depth','sector_name'],axis = 1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width=True
                                        )
                            
                        with bank2:
                            st.write(names[counter+1] +f'  F  : {int(F1.Final)}  ...  {round((int(F1.Final)/int(F1.Y_Final)-1)*100,2)}  _and_  Last : {int(F1.Close)} ... {round((int(F1.Close)/int(F1.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+1]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width= 1000,
                                        use_container_width=True
                                        )
                            
                        with bank3:
                            st.write(names[counter+2] +f'   F  : {int(F2.Final)}  ...  {round((int(F2.Final)/int(F2.Y_Final)-1)*100,2)}  _and_  Last : {int(F2.Close)}  ...  {round((int(F2.Close)/int(F2.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+2]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width=1000,
                                        use_container_width = True
                                        )
                        counter +=3
                            
                elif bourse_sector=="محصولات غذایی و آشامیدنی به جز قند و شکر":
                    debth = debth[debth.sector_name.str.contains("محصولات غذایی و آشامیدنی به جز قند و شکر")]
                    names = debth.Ticker.unique()
                    counter=0
                    st.subheader("**last update: {}**".format(get_time()))
                    for i_ in range(int(len(names)/3)):      
                        bank1, bank2, bank3 = st.columns([1,1,1],gap='small')
                        
                        F = market_price[market_price.Ticker == (names[counter])]
                        F1 = market_price[market_price.Ticker == (names[counter+1])]
                        F2 = market_price[market_price.Ticker == (names[counter+2])]
                        with bank1:
                            st.write(names[counter] +f'F  : {int(F.Final)}  ...  {round((int(F.Final)/int(F.Y_Final)-1)*100,2)}    _and_  Last : {int(F.Close)}  ...  {round((int(F.Close)/int(F.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter]].drop(['flow','Ticker','OB-Depth','sector_name'],axis = 1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width=True
                                        )
                            
                        with bank2:
                            st.write(names[counter+1] +f'  F  : {int(F1.Final)}  ...  {round((int(F1.Final)/int(F1.Y_Final)-1)*100,2)}  _and_  Last : {int(F1.Close)} ... {round((int(F1.Close)/int(F1.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+1]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width= 1000,
                                        use_container_width=True
                                        )
                            
                        with bank3:
                            st.write(names[counter+2] +f'   F  : {int(F2.Final)}  ...  {round((int(F2.Final)/int(F2.Y_Final)-1)*100,2)}  _and_  Last : {int(F2.Close)}  ...  {round((int(F2.Close)/int(F2.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+2]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width=1000,
                                        use_container_width = True
                                        )
                        counter +=3

                elif bourse_sector=="خودرو و ساخت قطعات":
                    debth = debth[debth.sector_name.str.contains("خودرو و ساخت قطعات")]
                    names = debth.Ticker.unique()
                    counter=0
                    st.subheader("**last update: {}**".format(get_time()))
                    for i_ in range(int(len(names)/3)):      
                        bank1, bank2, bank3 = st.columns([1,1,1],gap='small')
                        
                        F = market_price[market_price.Ticker == (names[counter])]
                        F1 = market_price[market_price.Ticker == (names[counter+1])]
                        F2 = market_price[market_price.Ticker == (names[counter+2])]
                        with bank1:
                            st.write(names[counter] +f'F  : {int(F.Final)}  ...  {round((int(F.Final)/int(F.Y_Final)-1)*100,2)}    _and_  Last : {int(F.Close)}  ...  {round((int(F.Close)/int(F.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter]].drop(['flow','Ticker','OB-Depth','sector_name'],axis = 1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width=True
                                        )
                            
                        with bank2:
                            st.write(names[counter+1] +f'  F  : {int(F1.Final)}  ...  {round((int(F1.Final)/int(F1.Y_Final)-1)*100,2)}  _and_  Last : {int(F1.Close)} ... {round((int(F1.Close)/int(F1.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+1]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width= 1000,
                                        use_container_width=True
                                        )
                            
                        with bank3:
                            st.write(names[counter+2] +f'   F  : {int(F2.Final)}  ...  {round((int(F2.Final)/int(F2.Y_Final)-1)*100,2)}  _and_  Last : {int(F2.Close)}  ...  {round((int(F2.Close)/int(F2.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+2]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width=1000,
                                        use_container_width = True
                                        )
                        counter +=3

                elif bourse_sector=="بیمه وصندوق بازنشستگی به جزتامین اجتماعی":
                    debth = debth[debth.sector_name.str.contains("بیمه وصندوق بازنشستگی به جزتامین اجتماعی")]
                    names = debth.Ticker.unique()
                    counter=0
                    st.subheader("**last update: {}**".format(get_time()))
                    for i_ in range(int(len(names)/3)):      
                        bank1, bank2, bank3 = st.columns([1,1,1],gap='small')
                        
                        F = market_price[market_price.Ticker == (names[counter])]
                        F1 = market_price[market_price.Ticker == (names[counter+1])]
                        F2 = market_price[market_price.Ticker == (names[counter+2])]
                        with bank1:
                            st.write(names[counter] +f'F  : {int(F.Final)}  ...  {round((int(F.Final)/int(F.Y_Final)-1)*100,2)}    _and_  Last : {int(F.Close)}  ...  {round((int(F.Close)/int(F.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter]].drop(['flow','Ticker','OB-Depth','sector_name'],axis = 1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width=True
                                        )
                            
                        with bank2:
                            st.write(names[counter+1] +f'  F  : {int(F1.Final)}  ...  {round((int(F1.Final)/int(F1.Y_Final)-1)*100,2)}  _and_  Last : {int(F1.Close)} ... {round((int(F1.Close)/int(F1.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+1]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width= 1000,
                                        use_container_width=True
                                        )
                            
                        with bank3:
                            st.write(names[counter+2] +f'   F  : {int(F2.Final)}  ...  {round((int(F2.Final)/int(F2.Y_Final)-1)*100,2)}  _and_  Last : {int(F2.Close)}  ...  {round((int(F2.Close)/int(F2.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+2]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width=1000,
                                        use_container_width = True
                                        )
                        counter +=3
                                                
                elif bourse_sector=="انبوه سازی، املاک و مستغلات":
                    debth = debth[debth.sector_name.str.contains("انبوه سازی، املاک و مستغلات")]
                    names = debth.Ticker.unique()
                    counter=0
                    st.subheader("**last update: {}**".format(get_time()))
                    for i_ in range(int(len(names)/3)):      
                        bank1, bank2, bank3 = st.columns([1,1,1],gap='small')
                        
                        F = market_price[market_price.Ticker == (names[counter])]
                        F1 = market_price[market_price.Ticker == (names[counter+1])]
                        F2 = market_price[market_price.Ticker == (names[counter+2])]
                        with bank1:
                            st.write(names[counter] +f'F  : {int(F.Final)}  ...  {round((int(F.Final)/int(F.Y_Final)-1)*100,2)}    _and_  Last : {int(F.Close)}  ...  {round((int(F.Close)/int(F.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter]].drop(['flow','Ticker','OB-Depth','sector_name'],axis = 1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width=True
                                        )
                            
                        with bank2:
                            st.write(names[counter+1] +f'  F  : {int(F1.Final)}  ...  {round((int(F1.Final)/int(F1.Y_Final)-1)*100,2)}  _and_  Last : {int(F1.Close)} ... {round((int(F1.Close)/int(F1.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+1]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width= 1000,
                                        use_container_width=True
                                        )
                            
                        with bank3:
                            st.write(names[counter+2] +f'   F  : {int(F2.Final)}  ...  {round((int(F2.Final)/int(F2.Y_Final)-1)*100,2)}  _and_  Last : {int(F2.Close)}  ...  {round((int(F2.Close)/int(F2.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+2]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width=1000,
                                        use_container_width = True
                                        )
                        counter +=3

                elif bourse_sector=="استخراج کانه های فلزی":
                    debth = debth[debth.sector_name.str.contains("استخراج کانه های فلزی")]
                    names = debth.Ticker.unique()
                    counter=0
                    st.subheader("**last update: {}**".format(get_time()))
                    for i_ in range(int(len(names)/3)):      
                        bank1, bank2, bank3 = st.columns([1,1,1],gap='small')
                        
                        F = market_price[market_price.Ticker == (names[counter])]
                        F1 = market_price[market_price.Ticker == (names[counter+1])]
                        F2 = market_price[market_price.Ticker == (names[counter+2])]
                        with bank1:
                            st.write(names[counter] +f'F  : {int(F.Final)}  ...  {round((int(F.Final)/int(F.Y_Final)-1)*100,2)}    _and_  Last : {int(F.Close)}  ...  {round((int(F.Close)/int(F.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter]].drop(['flow','Ticker','OB-Depth','sector_name'],axis = 1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width=True
                                        )
                            
                        with bank2:
                            st.write(names[counter+1] +f'  F  : {int(F1.Final)}  ...  {round((int(F1.Final)/int(F1.Y_Final)-1)*100,2)}  _and_  Last : {int(F1.Close)} ... {round((int(F1.Close)/int(F1.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+1]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width= 1000,
                                        use_container_width=True
                                        )
                            
                        with bank3:
                            st.write(names[counter+2] +f'   F  : {int(F2.Final)}  ...  {round((int(F2.Final)/int(F2.Y_Final)-1)*100,2)}  _and_  Last : {int(F2.Close)}  ...  {round((int(F2.Close)/int(F2.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+2]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width=1000,
                                        use_container_width = True
                                        )
                        counter +=3

                elif bourse_sector=="حمل ونقل، انبارداری و ارتباطات":
                    debth = debth[debth.sector_name.str.contains("حمل ونقل، انبارداری و ارتباطات")]
                    names = debth.Ticker.unique()
                    counter=0
                    st.subheader("**last update: {}**".format(get_time()))
                    for i_ in range(int(len(names)/3)):      
                        bank1, bank2, bank3 = st.columns([1,1,1],gap='small')
                        
                        F = market_price[market_price.Ticker == (names[counter])]
                        F1 = market_price[market_price.Ticker == (names[counter+1])]
                        F2 = market_price[market_price.Ticker == (names[counter+2])]
                        with bank1:
                            st.write(names[counter] +f'F  : {int(F.Final)}  ...  {round((int(F.Final)/int(F.Y_Final)-1)*100,2)}    _and_  Last : {int(F.Close)}  ...  {round((int(F.Close)/int(F.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter]].drop(['flow','Ticker','OB-Depth','sector_name'],axis = 1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width=True
                                        )
                            
                        with bank2:
                            st.write(names[counter+1] +f'  F  : {int(F1.Final)}  ...  {round((int(F1.Final)/int(F1.Y_Final)-1)*100,2)}  _and_  Last : {int(F1.Close)} ... {round((int(F1.Close)/int(F1.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+1]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width= 1000,
                                        use_container_width=True
                                        )
                            
                        with bank3:
                            st.write(names[counter+2] +f'   F  : {int(F2.Final)}  ...  {round((int(F2.Final)/int(F2.Y_Final)-1)*100,2)}  _and_  Last : {int(F2.Close)}  ...  {round((int(F2.Close)/int(F2.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+2]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width=1000,
                                        use_container_width = True
                                        )
                        counter +=3
                                                     
                elif bourse_sector=="فراورده های نفتی، کک و سوخت هسته ای":
                    debth = debth[debth.sector_name.str.contains("فراورده های نفتی، کک و سوخت هسته ای")]
                    names = debth.Ticker.unique()
                    counter=0
                    st.subheader("**last update: {}**".format(get_time()))
                    for i_ in range(int(len(names)/3)):      
                        bank1, bank2, bank3 = st.columns([1,1,1],gap='small')
                        
                        F = market_price[market_price.Ticker == (names[counter])]
                        F1 = market_price[market_price.Ticker == (names[counter+1])]
                        F2 = market_price[market_price.Ticker == (names[counter+2])]
                        with bank1:
                            st.write(names[counter] +f'F  : {int(F.Final)}  ...  {round((int(F.Final)/int(F.Y_Final)-1)*100,2)}    _and_  Last : {int(F.Close)}  ...  {round((int(F.Close)/int(F.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter]].drop(['flow','Ticker','OB-Depth','sector_name'],axis = 1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width=True
                                        )
                            
                        with bank2:
                            st.write(names[counter+1] +f'  F  : {int(F1.Final)}  ...  {round((int(F1.Final)/int(F1.Y_Final)-1)*100,2)}  _and_  Last : {int(F1.Close)} ... {round((int(F1.Close)/int(F1.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+1]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width= 1000,
                                        use_container_width=True
                                        )
                            
                        with bank3:
                            st.write(names[counter+2] +f'   F  : {int(F2.Final)}  ...  {round((int(F2.Final)/int(F2.Y_Final)-1)*100,2)}  _and_  Last : {int(F2.Close)}  ...  {round((int(F2.Close)/int(F2.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+2]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width=1000,
                                        use_container_width = True
                                        )
                        counter +=3

                elif bourse_sector=="اطلاعات و ارتباطات":
                    debth = debth[debth.sector_name.str.contains("اطلاعات و ارتباطات")]
                    names = debth.Ticker.unique()
                    counter=0
                    st.subheader("**last update: {}**".format(get_time()))
                    for i_ in range(int(len(names)/3)):      
                        bank1, bank2, bank3 = st.columns([1,1,1],gap='small')
                        
                        F = market_price[market_price.Ticker == (names[counter])]
                        F1 = market_price[market_price.Ticker == (names[counter+1])]
                        F2 = market_price[market_price.Ticker == (names[counter+2])]
                        with bank1:
                            st.write(names[counter] +f'F  : {int(F.Final)}  ...  {round((int(F.Final)/int(F.Y_Final)-1)*100,2)}    _and_  Last : {int(F.Close)}  ...  {round((int(F.Close)/int(F.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter]].drop(['flow','Ticker','OB-Depth','sector_name'],axis = 1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width=True
                                        )
                            
                        with bank2:
                            st.write(names[counter+1] +f'  F  : {int(F1.Final)}  ...  {round((int(F1.Final)/int(F1.Y_Final)-1)*100,2)}  _and_  Last : {int(F1.Close)} ... {round((int(F1.Close)/int(F1.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+1]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width= 1000,
                                        use_container_width=True
                                        )
                            
                        with bank3:
                            st.write(names[counter+2] +f'   F  : {int(F2.Final)}  ...  {round((int(F2.Final)/int(F2.Y_Final)-1)*100,2)}  _and_  Last : {int(F2.Close)}  ...  {round((int(F2.Close)/int(F2.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+2]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width=1000,
                                        use_container_width = True
                                        )
                        counter +=3

                elif bourse_sector=="قند و شکر":
                    debth = debth[debth.sector_name.str.contains("قند و شکر")]
                    names = debth.Ticker.unique()
                    counter=0
                    st.subheader("**last update: {}**".format(get_time()))
                    for i_ in range(int(len(names)/3)):      
                        bank1, bank2, bank3 = st.columns([1,1,1],gap='small')
                        
                        F = market_price[market_price.Ticker == (names[counter])]
                        F1 = market_price[market_price.Ticker == (names[counter+1])]
                        F2 = market_price[market_price.Ticker == (names[counter+2])]
                        with bank1:
                            st.write(names[counter] +f'F  : {int(F.Final)}  ...  {round((int(F.Final)/int(F.Y_Final)-1)*100,2)}    _and_  Last : {int(F.Close)}  ...  {round((int(F.Close)/int(F.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter]].drop(['flow','Ticker','OB-Depth','sector_name'],axis = 1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width=True
                                        )
                            
                        with bank2:
                            st.write(names[counter+1] +f'  F  : {int(F1.Final)}  ...  {round((int(F1.Final)/int(F1.Y_Final)-1)*100,2)}  _and_  Last : {int(F1.Close)} ... {round((int(F1.Close)/int(F1.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+1]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width= 1000,
                                        use_container_width=True
                                        )
                            
                        with bank3:
                            st.write(names[counter+2] +f'   F  : {int(F2.Final)}  ...  {round((int(F2.Final)/int(F2.Y_Final)-1)*100,2)}  _and_  Last : {int(F2.Close)}  ...  {round((int(F2.Close)/int(F2.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+2]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width=1000,
                                        use_container_width = True
                                        )
                        counter +=3
                                                     
                elif bourse_sector=="سایر محصولات کانی غیرفلزی":
                    debth = debth[debth.sector_name.str.contains("سایر محصولات کانی غیرفلزی")]
                    names = debth.Ticker.unique()
                    counter=0
                    st.subheader("**last update: {}**".format(get_time()))
                    for i_ in range(int(len(names)/3)):      
                        bank1, bank2, bank3 = st.columns([1,1,1],gap='small')
                        
                        F = market_price[market_price.Ticker == (names[counter])]
                        F1 = market_price[market_price.Ticker == (names[counter+1])]
                        F2 = market_price[market_price.Ticker == (names[counter+2])]
                        with bank1:
                            st.write(names[counter] +f'F  : {int(F.Final)}  ...  {round((int(F.Final)/int(F.Y_Final)-1)*100,2)}    _and_  Last : {int(F.Close)}  ...  {round((int(F.Close)/int(F.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter]].drop(['flow','Ticker','OB-Depth','sector_name'],axis = 1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width=True
                                        )
                            
                        with bank2:
                            st.write(names[counter+1] +f'  F  : {int(F1.Final)}  ...  {round((int(F1.Final)/int(F1.Y_Final)-1)*100,2)}  _and_  Last : {int(F1.Close)} ... {round((int(F1.Close)/int(F1.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+1]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width= 1000,
                                        use_container_width=True
                                        )
                            
                        with bank3:
                            st.write(names[counter+2] +f'   F  : {int(F2.Final)}  ...  {round((int(F2.Final)/int(F2.Y_Final)-1)*100,2)}  _and_  Last : {int(F2.Close)}  ...  {round((int(F2.Close)/int(F2.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+2]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width=1000,
                                        use_container_width = True
                                        )
                        counter +=3

                elif bourse_sector=="واسطه گری های مالی و پولی":
                    debth = debth[debth.sector_name.str.contains("واسطه گری های مالی و پولی")]
                    names = debth.Ticker.unique()
                    counter=0
                    st.subheader("**last update: {}**".format(get_time()))
                    for i_ in range(int(len(names)/3)):      
                        bank1, bank2, bank3 = st.columns([1,1,1],gap='small')
                        
                        F = market_price[market_price.Ticker == (names[counter])]
                        F1 = market_price[market_price.Ticker == (names[counter+1])]
                        F2 = market_price[market_price.Ticker == (names[counter+2])]
                        with bank1:
                            st.write(names[counter] +f'F  : {int(F.Final)}  ...  {round((int(F.Final)/int(F.Y_Final)-1)*100,2)}    _and_  Last : {int(F.Close)}  ...  {round((int(F.Close)/int(F.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter]].drop(['flow','Ticker','OB-Depth','sector_name'],axis = 1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width=True
                                        )
                            
                        with bank2:
                            st.write(names[counter+1] +f'  F  : {int(F1.Final)}  ...  {round((int(F1.Final)/int(F1.Y_Final)-1)*100,2)}  _and_  Last : {int(F1.Close)} ... {round((int(F1.Close)/int(F1.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+1]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width= 1000,
                                        use_container_width=True
                                        )
                            
                        with bank3:
                            st.write(names[counter+2] +f'   F  : {int(F2.Final)}  ...  {round((int(F2.Final)/int(F2.Y_Final)-1)*100,2)}  _and_  Last : {int(F2.Close)}  ...  {round((int(F2.Close)/int(F2.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+2]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width=1000,
                                        use_container_width = True
                                        )
                        counter +=3

                elif bourse_sector=="استخراج نفت گاز و خدمات جنبی جز اکتشاف":
                    debth = debth[debth.sector_name.str.contains("استخراج نفت گاز و خدمات جنبی جز اکتشاف")]
                    names = debth.Ticker.unique()
                    counter=0
                    st.subheader("**last update: {}**".format(get_time()))
                    for i_ in range(int(len(names)/3)):      
                        bank1, bank2, bank3 = st.columns([1,1,1],gap='small')
                        
                        F = market_price[market_price.Ticker == (names[counter])]
                        F1 = market_price[market_price.Ticker == (names[counter+1])]
                        F2 = market_price[market_price.Ticker == (names[counter+2])]
                        with bank1:
                            st.write(names[counter] +f'F  : {int(F.Final)}  ...  {round((int(F.Final)/int(F.Y_Final)-1)*100,2)}    _and_  Last : {int(F.Close)}  ...  {round((int(F.Close)/int(F.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter]].drop(['flow','Ticker','OB-Depth','sector_name'],axis = 1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width=True
                                        )
                            
                        with bank2:
                            st.write(names[counter+1] +f'  F  : {int(F1.Final)}  ...  {round((int(F1.Final)/int(F1.Y_Final)-1)*100,2)}  _and_  Last : {int(F1.Close)} ... {round((int(F1.Close)/int(F1.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+1]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width= 1000,
                                        use_container_width=True
                                        )
                            
                        with bank3:
                            st.write(names[counter+2] +f'   F  : {int(F2.Final)}  ...  {round((int(F2.Final)/int(F2.Y_Final)-1)*100,2)}  _and_  Last : {int(F2.Close)}  ...  {round((int(F2.Close)/int(F2.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+2]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width=1000,
                                        use_container_width = True
                                        )
                        counter +=3
                                                       
                elif bourse_sector=="استخراج سایر معادن":
                    debth = debth[debth.sector_name.str.contains("استخراج سایر معادن")]
                    names = debth.Ticker.unique()
                    counter=0
                    st.subheader("**last update: {}**".format(get_time()))
                    for i_ in range(int(len(names)/3)):      
                        bank1, bank2, bank3 = st.columns([1,1,1],gap='small')
                        F = market_price[market_price.Ticker == (names[counter])]
                        F1 = market_price[market_price.Ticker == (names[counter+1])]
                        F2 = market_price[market_price.Ticker == (names[counter+2])]
                        with bank1:
                            st.write(names[counter] +f'F  : {int(F.Final)}  ...  {round((int(F.Final)/int(F.Y_Final)-1)*100,2)}    _and_  Last : {int(F.Close)}  ...  {round((int(F.Close)/int(F.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter]].drop(['flow','Ticker','OB-Depth','sector_name'],axis = 1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width=True
                                        )
                            
                        with bank2:
                            st.write(names[counter+1] +f'  F  : {int(F1.Final)}  ...  {round((int(F1.Final)/int(F1.Y_Final)-1)*100,2)}  _and_  Last : {int(F1.Close)} ... {round((int(F1.Close)/int(F1.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+1]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width= 1000,
                                        use_container_width=True
                                        )
                            
                        with bank3:
                            st.write(names[counter+2] +f'   F  : {int(F2.Final)}  ...  {round((int(F2.Final)/int(F2.Y_Final)-1)*100,2)}  _and_  Last : {int(F2.Close)}  ...  {round((int(F2.Close)/int(F2.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+2]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width=1000,
                                        use_container_width = True
                                        )
                        counter +=3

                elif bourse_sector=="پیمانکاری صنعتی":
                    debth = debth[debth.sector_name.str.contains("پیمانکاری صنعتی")]
                    names = debth.Ticker.unique()
                    counter=0
                    st.subheader("**last update: {}**".format(get_time()))
                    for i_ in range(int(len(names)/3)):      
                        bank1, bank2, bank3 = st.columns([1,1,1],gap='small')
                        
                        F = market_price[market_price.Ticker == (names[counter])]
                        F1 = market_price[market_price.Ticker == (names[counter+1])]
                        F2 = market_price[market_price.Ticker == (names[counter+2])]
                        with bank1:
                            st.write(names[counter] +f'F  : {int(F.Final)}  ...  {round((int(F.Final)/int(F.Y_Final)-1)*100,2)}    _and_  Last : {int(F.Close)}  ...  {round((int(F.Close)/int(F.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter]].drop(['flow','Ticker','OB-Depth','sector_name'],axis = 1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width=True
                                        )
                            
                        with bank2:
                            st.write(names[counter+1] +f'  F  : {int(F1.Final)}  ...  {round((int(F1.Final)/int(F1.Y_Final)-1)*100,2)}  _and_  Last : {int(F1.Close)} ... {round((int(F1.Close)/int(F1.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+1]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width= 1000,
                                        use_container_width=True
                                        )
                            
                        with bank3:
                            st.write(names[counter+2] +f'   F  : {int(F2.Final)}  ...  {round((int(F2.Final)/int(F2.Y_Final)-1)*100,2)}  _and_  Last : {int(F2.Close)}  ...  {round((int(F2.Close)/int(F2.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+2]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width=1000,
                                        use_container_width = True
                                        )
                        counter +=3

                elif bourse_sector=="ماشین آلات و تجهیزات":
                    debth = debth[debth.sector_name.str.contains("ماشین آلات و تجهیزات")]
                    names = debth.Ticker.unique()
                    counter=0
                    st.subheader("**last update: {}**".format(get_time()))
                    for i_ in range(int(len(names)/3)):      
                        bank1, bank2, bank3 = st.columns([1,1,1],gap='small')
                        
                        F = market_price[market_price.Ticker == (names[counter])]
                        F1 = market_price[market_price.Ticker == (names[counter+1])]
                        F2 = market_price[market_price.Ticker == (names[counter+2])]
                        with bank1:
                            st.write(names[counter] +f'F  : {int(F.Final)}  ...  {round((int(F.Final)/int(F.Y_Final)-1)*100,2)}    _and_  Last : {int(F.Close)}  ...  {round((int(F.Close)/int(F.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter]].drop(['flow','Ticker','OB-Depth','sector_name'],axis = 1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width=True
                                        )
                            
                        with bank2:
                            st.write(names[counter+1] +f'  F  : {int(F1.Final)}  ...  {round((int(F1.Final)/int(F1.Y_Final)-1)*100,2)}  _and_  Last : {int(F1.Close)} ... {round((int(F1.Close)/int(F1.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+1]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width= 1000,
                                        use_container_width=True
                                        )
                            
                        with bank3:
                            st.write(names[counter+2] +f'   F  : {int(F2.Final)}  ...  {round((int(F2.Final)/int(F2.Y_Final)-1)*100,2)}  _and_  Last : {int(F2.Close)}  ...  {round((int(F2.Close)/int(F2.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+2]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width=1000,
                                        use_container_width = True
                                        )
                        counter +=3
                    
                elif bourse_sector=="ماشین آلات و دستگاه های برقی":
                    debth = debth[debth.sector_name.str.contains("ماشین آلات و دستگاه های برقی")]
                    names = debth.Ticker.unique()
                    counter=0
                    st.subheader("**last update: {}**".format(get_time()))
                    for i_ in range(int(len(names)/3)):      
                        bank1, bank2, bank3 = st.columns([1,1,1],gap='small')
                        
                        F = market_price[market_price.Ticker == (names[counter])]
                        F1 = market_price[market_price.Ticker == (names[counter+1])]
                        F2 = market_price[market_price.Ticker == (names[counter+2])]
                        with bank1:
                            st.write(names[counter] +f'F  : {int(F.Final)}  ...  {round((int(F.Final)/int(F.Y_Final)-1)*100,2)}    _and_  Last : {int(F.Close)}  ...  {round((int(F.Close)/int(F.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter]].drop(['flow','Ticker','OB-Depth','sector_name'],axis = 1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width=True
                                        )
                            
                        with bank2:
                            st.write(names[counter+1] +f'  F  : {int(F1.Final)}  ...  {round((int(F1.Final)/int(F1.Y_Final)-1)*100,2)}  _and_  Last : {int(F1.Close)} ... {round((int(F1.Close)/int(F1.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+1]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width= 1000,
                                        use_container_width=True
                                        )
                            
                        with bank3:
                            st.write(names[counter+2] +f'   F  : {int(F2.Final)}  ...  {round((int(F2.Final)/int(F2.Y_Final)-1)*100,2)}  _and_  Last : {int(F2.Close)}  ...  {round((int(F2.Close)/int(F2.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+2]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width=1000,
                                        use_container_width = True
                                        )
                        counter +=3
                
                elif bourse_sector=="حمل و نقل آبی":
                    debth = debth[debth.sector_name.str.contains("حمل و نقل آبی")]
                    names = debth.Ticker.unique()
                    counter=0
                    st.subheader("**last update: {}**".format(get_time()))
                    for i_ in range(int(len(names)/3)):      
                        bank1, bank2, bank3 = st.columns([1,1,1],gap='small')
                        
                        F = market_price[market_price.Ticker == (names[counter])]
                        F1 = market_price[market_price.Ticker == (names[counter+1])]
                        F2 = market_price[market_price.Ticker == (names[counter+2])]
                        with bank1:
                            st.write(names[counter] +f'F  : {int(F.Final)}  ...  {round((int(F.Final)/int(F.Y_Final)-1)*100,2)}    _and_  Last : {int(F.Close)}  ...  {round((int(F.Close)/int(F.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter]].drop(['flow','Ticker','OB-Depth','sector_name'],axis = 1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width=True
                                        )
                            
                        with bank2:
                            st.write(names[counter+1] +f'  F  : {int(F1.Final)}  ...  {round((int(F1.Final)/int(F1.Y_Final)-1)*100,2)}  _and_  Last : {int(F1.Close)} ... {round((int(F1.Close)/int(F1.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+1]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width= 1000,
                                        use_container_width=True
                                        )
                            
                        with bank3:
                            st.write(names[counter+2] +f'   F  : {int(F2.Final)}  ...  {round((int(F2.Final)/int(F2.Y_Final)-1)*100,2)}  _and_  Last : {int(F2.Close)}  ...  {round((int(F2.Close)/int(F2.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+2]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width=1000,
                                        use_container_width = True
                                        )
                        counter +=3

                elif bourse_sector=="رایانه و فعالیت های وابسته به آن":
                    debth = debth[debth.sector_name.str.contains("رایانه و فعالیت های وابسته به آن")]
                    names = debth.Ticker.unique()
                    counter=0
                    st.subheader("**last update: {}**".format(get_time()))
                    for i_ in range(int(len(names)/3)):      
                        bank1, bank2, bank3 = st.columns([1,1,1],gap='small')
                        
                        F = market_price[market_price.Ticker == (names[counter])]
                        F1 = market_price[market_price.Ticker == (names[counter+1])]
                        F2 = market_price[market_price.Ticker == (names[counter+2])]
                        with bank1:
                            st.write(names[counter] +f'F  : {int(F.Final)}  ...  {round((int(F.Final)/int(F.Y_Final)-1)*100,2)}    _and_  Last : {int(F.Close)}  ...  {round((int(F.Close)/int(F.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter]].drop(['flow','Ticker','OB-Depth','sector_name'],axis = 1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width=True
                                        )
                            
                        with bank2:
                            st.write(names[counter+1] +f'  F  : {int(F1.Final)}  ...  {round((int(F1.Final)/int(F1.Y_Final)-1)*100,2)}  _and_  Last : {int(F1.Close)} ... {round((int(F1.Close)/int(F1.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+1]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width= 1000,
                                        use_container_width=True
                                        )
                            
                        with bank3:
                            st.write(names[counter+2] +f'   F  : {int(F2.Final)}  ...  {round((int(F2.Final)/int(F2.Y_Final)-1)*100,2)}  _and_  Last : {int(F2.Close)}  ...  {round((int(F2.Close)/int(F2.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+2]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width=1000,
                                        use_container_width = True
                                        )
                        counter +=3

                elif bourse_sector=="زراعت و خدمات وابسته":
                    debth = debth[debth.sector_name.str.contains("زراعت و خدمات وابسته")]
                    names = debth.Ticker.unique()
                    counter=0
                    st.subheader("**last update: {}**".format(get_time()))
                    for i_ in range(int(len(names)/3)):      
                        bank1, bank2, bank3 = st.columns([1,1,1],gap='small')
                        
                        F = market_price[market_price.Ticker == (names[counter])]
                        F1 = market_price[market_price.Ticker == (names[counter+1])]
                        F2 = market_price[market_price.Ticker == (names[counter+2])]
                        with bank1:
                            st.write(names[counter] +f'F  : {int(F.Final)}  ...  {round((int(F.Final)/int(F.Y_Final)-1)*100,2)}    _and_  Last : {int(F.Close)}  ...  {round((int(F.Close)/int(F.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter]].drop(['flow','Ticker','OB-Depth','sector_name'],axis = 1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        use_container_width=True
                                        )
                            
                        with bank2:
                            st.write(names[counter+1] +f'  F  : {int(F1.Final)}  ...  {round((int(F1.Final)/int(F1.Y_Final)-1)*100,2)}  _and_  Last : {int(F1.Close)} ... {round((int(F1.Close)/int(F1.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+1]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width= 1000,
                                        use_container_width=True
                                        )
                            
                        with bank3:
                            st.write(names[counter+2] +f'   F  : {int(F2.Final)}  ...  {round((int(F2.Final)/int(F2.Y_Final)-1)*100,2)}  _and_  Last : {int(F2.Close)}  ...  {round((int(F2.Close)/int(F2.Y_Final)-1)*100,2)}')
                            st.dataframe(debth[debth.Ticker == names[counter+2]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                            .style.applymap(green_highlight, subset=['B_P'])
                                            .applymap(red_highlight, subset=['S_P']),
                                        hide_index=True,
                                        #width=1000,
                                        use_container_width = True
                                        )
                        counter +=3

        elif (bourse_choices== 'عمق بازار') and (stock_or_sector == 'پرتفوی 6 تایی'):
            debth = debth.drop('WEB-ID',axis=1)
            with placeholder2.container():
                counter=0
                st.subheader("**last update: {}**".format(get_time()))
                for i_ in range(int(len(d_stock)/3)):      
                    bank1, bank2, bank3 = st.columns([1,1,1],gap='small')
                    F = market_price[market_price.Ticker == (d_stock[counter])]
                    F1 = market_price[market_price.Ticker == (d_stock[counter+1])]
                    F2 = market_price[market_price.Ticker == (d_stock[counter+2])]
                    with bank1:
                        st.write(d_stock[counter] +f'F  : {int(F.Final)}  ...  {round((int(F.Final)/int(F.Y_Final)-1)*100,2)}    _and_  Last : {int(F.Close)}  ...  {round((int(F.Close)/int(F.Y_Final)-1)*100,2)}')
                        st.dataframe(debth[debth.Ticker == d_stock[counter]].drop(['flow','Ticker','OB-Depth','sector_name'],axis = 1)
                                        .style.applymap(green_highlight, subset=['B_P'])
                                        .applymap(red_highlight, subset=['S_P']),
                                    hide_index=True,
                                    use_container_width=True
                                    )
                    with bank2:
                        st.write(d_stock[counter+1] +f'  F  : {int(F1.Final)}  ...  {round((int(F1.Final)/int(F1.Y_Final)-1)*100,2)}  _and_  Last : {int(F1.Close)} ... {round((int(F1.Close)/int(F1.Y_Final)-1)*100,2)}')
                        st.dataframe(debth[debth.Ticker == d_stock[counter+1]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                        .style.applymap(green_highlight, subset=['B_P'])
                                        .applymap(red_highlight, subset=['S_P']),
                                    hide_index=True,
                                    use_container_width=True
                                    )   
                    with bank3:
                        st.write(d_stock[counter+2] +f'   F  : {int(F2.Final)}  ...  {round((int(F2.Final)/int(F2.Y_Final)-1)*100,2)}  _and_  Last : {int(F2.Close)}  ...  {round((int(F2.Close)/int(F2.Y_Final)-1)*100,2)}')
                        st.dataframe(debth[debth.Ticker== d_stock[counter+2]].drop(['flow','Ticker','OB-Depth','sector_name'],axis =1)
                                        .style.applymap(green_highlight, subset=['B_P'])
                                        .applymap(red_highlight, subset=['S_P']),
                                    hide_index=True,
                                    use_container_width = True
                                    )
                    counter +=3
           
        elif bourse_choices == 'اطلاعات کلی':
            
            data_ = total_info(req,market_sector_pd_for_map,need__)
            #  cleaning data from bloki and fixed income
            filtered_data = data_[data_['Trade Type'] == 'تابلو']
            add_filtred_data = add_column(filtered_data)
            select = add_filtred_data[add_filtred_data['sector_name'] == 'صندوق سرمایه گذاری قابل معامله']
            add_filtred_data.loc[select.index, 'sector_name'] = select['Name'].apply(get_fix_stock_etfs)
            data = add_filtred_data[add_filtred_data['sector_name'] != ('صندوق درآمد ثابت')]
            # now with others 
            data = data[data['sector_name'] != ('سایر صندوق‌ها')]
            # creating KPIs
            fixed_income = add_filtred_data[add_filtred_data['sector_name'] == ('صندوق درآمد ثابت')]
            entrence_of_fixed = round(fixed_income['Balance_R'].sum())
            
            R_Power_Buy = round(data['Power_Buy_R'].mean()* 1000)
            R_Power_Sell = round(data['Power_Sell_R'].mean()* 1000)
            Money_Entrance = round(data['Balance_R'].sum())
            Retail_Value = float(data['Value'].sum()/10**13)
            P_Final_Stock_Number = len(data[data['Final(%)']>0])/len(data)
            P_Close_Stock_Number = len(data[data['Close(%)']>0])/len(data)
            with placeholder.container():
                st.markdown("**last update: {}**".format(get_time()))

                # create three columns
                R_Power_Buy_, R_Power_Sell_, Money_Entrance_,Retail_Value_,P_Final_Stock_Number_,P_Close_Stock_Number_ ,fixedd= st.columns(7)

                # fill in those three columns with respective metrics or KPIs
                fixedd.metric(
                    label="Entrence of fixed incomes",
                    value=(entrence_of_fixed),
                )
                R_Power_Buy_.metric(
                    label="R_Power_Buy",
                    value=(R_Power_Buy),
                    #delta=df.iloc[-1]['Close'] - df.iloc[0]['Close'],
                )
                
                R_Power_Sell_.metric(
                    label="R_Power_Sell",
                    value=round(R_Power_Sell),
                )
                
                Money_Entrance_.metric(
                    label="Money_Entrance",
                    value=round(Money_Entrance),
                )
                Retail_Value_.metric(
                    label="Retail_Value",
                    value=round(Retail_Value, 2),
                )
                
                P_Final_Stock_Number_.metric(
                    label="P_Final_Stock_Number",
                    value=round(P_Final_Stock_Number, 2),
                )
                
                P_Close_Stock_Number_.metric(
                    label="P_Close_Stock_Number",
                    value=round(P_Close_Stock_Number, 2),
                )

                # create two columns for charts
                fig_col1, fig_col2 = st.columns(2)
                with fig_col1:
                    st.markdown("### buy_sell_RI")
                    fig = plot_buy_sell_RI(data)
                    st.write(fig)
                    
                with fig_col2:
                    st.markdown("### Money-Entrance")
                    fig2 = px.bar(add_filtred_data.groupby('sector_name')[['Balance_R']].sum().sort_values('Balance_R', ascending = False))
                    st.write(fig2)
                    
                fig_col3 = st.columns(1)
                with fig_col1:
                    st.markdown("#### Return By Sector")
                    fig = px.bar(
                                add_filtred_data.groupby('sector_name')[['Market Cap']]
                                .sum()
                                .sort_values('Market Cap', ascending = False)
                                .merge(
                                    data_.groupby('sector_name')[['Close(%)']].mean().sort_values('Close(%)', ascending = False),
                                    on = ['sector_name'])
                                .rename({'Close(%)': 'Mean Close(%)'}, axis=1),
                                y = 'Mean Close(%)',
                                barmode='group'
                                )
                    st.write(fig)
                
            
                
                


