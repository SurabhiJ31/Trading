import nsefin
import streamlit as st
from service_provider import get_companies_service
import requests

comp_service=get_companies_service()



def get_fno_list():
    return ['MANKIND', 'TIINDIA', 'OFSS', 'IDFCFIRSTB', 'TMPV', 'FORTIS', 'JSWENERGY', 'SOLARINDS', 'CGPOWER', 'BEL', 'BDL', 'POWERINDIA', 'BANDHANBNK', 'PERSISTENT', 'MAXHEALTH', 'POLYCAB', 'ALKEM', 'BANKBARODA', 'AUROPHARMA', 'OIL', 'PRESTIGE', 'ZYDUSLIFE', 'EICHERMOT', 'IDEA', 'ADANIPORTS', 'NMDC', 'HINDPETRO', 'UPL', 'PETRONET', 'ONGC', 'MAZDOCK', 'KEI', 'LUPIN', 'TCS', 'KPITTECH', 'SUNPHARMA', 'VOLTAS', 'MOTHERSON', 'LAURUSLABS', 'DELHIVERY', 'ICICIPRULI', 'PIIND', 'BLUESTARCO', 'RELIANCE', 'GLENMARK', 'HAL', 'BSE', 'IOC', 'YESBANK', 'PHOENIXLTD', 'UNOMINDA', 'MARUTI', 'ICICIBANK', 'DRREDDY', 'SHRIRAMFIN', 'CIPLA', 'CUMMINSIND', 'DABUR', 'VEDL', 'TECHM', 'SBILIFE', 'PIDILITIND', 'INDUSINDBK', 'HDFCAMC', 'ADANIENSOL', 'ABCAPITAL', 'KAYNES', 'BAJFINANCE', 'WAAREEENER', 'INFY', 'OBEROIRLTY', 'PNBHOUSING', 'RVNL', 'DIVISLAB', 'VBL', 'HCLTECH', 'HDFCLIFE', 'NATIONALUM', 'TATATECH', 'MPHASIS', 'HINDALCO', 'SAIL', 'JSWSTEEL', 'ASTRAL', 'JINDALSTEL', 'NAUKRI', 'POLICYBZR', 'HINDUNILVR', 'DLF', 'BHARTIARTL', 'BAJAJ-AUTO', 'INDHOTEL', 'JIOFIN', 'BPCL', 'COLPAL', 'AMBUJACEM', 'TORNTPHARM', 'HEROMOTOCO', 'PGEL', 'TITAN', 'TVSMOTOR', 'LT', 'ETERNAL', 'INDUSTOWER', 'FEDERALBNK', 'INOXWIND', 'KOTAKBANK', 'NUVAMA', 'BAJAJFINSV', 'UNIONBANK', 'ADANIGREEN', 'TATASTEEL', 'ASHOKLEY', 'BANKINDIA', 'GODREJCP', 'BHEL', 'TATAPOWER', 'IEX', 'INDIGO', 'KALYANKJIL', 'PPLPHARMA', 'ABB', 'SIEMENS', 'PNB', 'BOSCHLTD', 'ITC', 'ICICIGI', 'APOLLOHOSP', 'HINDZINC', 'DALBHARAT', 'SYNGENE', 'SUZLON', 'NYKAA', 'SHREECEM', 'EXIDEIND', 'BHARATFORG', 'M&M', '360ONE', 'INDIANB', 'SRF', 'SBIN', 'GAIL', 'GRASIM', 'COFORGE', 'SWIGGY', 'MARICO', 'RECLTD', 'GMRAIRPORT', 'NHPC', 'MFSL', 'NBCC', 'GODREJPROP', 'HDFCBANK', 'HAVELLS', 'NESTLEIND', 'CONCOR', 'CROMPTON', 'LICI', 'AUBANK', 'JUBLFOOD', 'LICHSGFIN', 'RBLBANK', 'AXISBANK', 'TORNTPOWER', 'SONACOMS', 'APLAPOLLO', 'PAYTM', 'WIPRO', 'IREDA', 'TATAELXSI', 'ULTRACEMCO', 'ASIANPAINT', 'AMBER', 'ADANIENT', 'TATACONSUM', 'NTPC', 'BRITANNIA', 'LTIM', 'PAGEIND', 'SUPREMEIND', 'DMART', 'KFINTECH', 'CANBK', 'CAMS', 'HUDCO', 'IRFC', 'COALINDIA', 'POWERGRID', 'PFC', 'BIOCON', 'TRENT', 'MCX', 'BAJAJHLDNG', 'PREMIERENE', 'LODHA', 'DIXON', 'PATANJALI', 'LTF', 'MUTHOOTFIN', 'SAMMAANCAP', 'SBICARD', 'UNITDSPR', 'CHOLAFIN', 'CDSL', 'MANAPPURAM', 'ANGELONE']

# @st.cache_data
# def get_fno_list():
#     nse = nsefin.NSEClient()
#     fno_stocks = nse.get_fno_list()
#     return list(fno_stocks['symbol'])

#company is symbol
def has_fno(company):
    return company in get_fno_list()

@st.cache_data
def get_companies_with_fno():
    all_fno_list = get_fno_list()
    all_companies = comp_service.get_company_symbols()
    res = list(set(all_fno_list) & set(all_companies))
    return res

@st.cache_data
def get_fno_companies_normalised():
    fno_normalised={}
    for cmp in get_companies_with_fno():
        fno_normalised[comp_service.normalize_name(comp_service.get_company_name(cmp))]=cmp
    return fno_normalised
