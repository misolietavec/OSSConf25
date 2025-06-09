import marimo as mo
import json
import geopandas as gp
import polars as pl
import plotly.express as px
import numpy as np


abbrev = {'Slovakia': 'SK', 'Poland': 'PL', 'Czechia': 'CZ', 'Hungary': 'HU'}

geo = json.load(open('converted_simp2.geojson','r'))

unemp = gp.read_file('converted_simp2.geojson', read_geometry=False)
unemp = unemp[['lau', 'name', 'registered_unemployed', 'Y15-64','population_density']]
unemp = pl.from_pandas(unemp)
unemp = unemp.with_columns((100 * pl.col('registered_unemployed') / pl.col('Y15-64')).alias('perc_unemp').round(2))

g_pars = {'SK': {'center': {"lon": 19.3, "lat": 48.7}, 'zoom': 6, 'w': 750, 'h': 400},
          'HU': {'center': {"lon": 19.3, "lat": 47.1}, 'zoom': 6, 'w': 750, 'h': 500},
          'PL': {'center': {"lon": 18.9, "lat": 51.9}, 'zoom': 5, 'w': 700, 'h': 500},
          'CZ': {'center': {"lon": 15.9, "lat": 49.7}, 'zoom': 6, 'w': 750, 'h': 500},
         }

def get_country_mapdata(cstr):
    if not cstr in g_pars.keys():
        return
    gf = geo['features']
    geo_cf = [p for p in gf if p['properties']['lau'][:2] == cstr]
    geo_c = {'type': 'FeatureCollection', 'name': f'Krajina {cstr}', 'features': geo_cf}
    unemp_c = unemp.filter(pl.col('lau').str.starts_with(cstr))
    return geo_c, unemp_c

u_pars = {k: get_country_mapdata(k) for k in g_pars.keys()}

def get_country_unemp_history(cstr):
    if not cstr in g_pars.keys():
        return   
    unemp_hist = pl.read_csv('lau1-history-iz.csv', 
    columns=["period", "lau", "name", "registered_unemployed",
             "registered_unemployed_females", "Y15-64", "Y15-64-females",
             "TOTAL"])
    unemp_hist = unemp_hist.with_columns((100 * pl.col('registered_unemployed') / pl.col('Y15-64')).alias('perc_unemp').round(2))         
    unemp_hc = unemp_hist.filter(pl.col('lau').str.starts_with(cstr))
    return unemp_hc

h_pars = {k: get_country_unemp_history(k) for k in g_pars.keys()}
    
def plot_map(cstr, column='perc_unemp'):
    geo_c, unemp_c = u_pars[cstr]
    lab_dict = {'perc_unemp': 'Unemp. %', 'population_density': 'Pop. dens.'}
    nmax = 1.1 * unemp_c[column].max()
    nmin = 1.1 * unemp_c[column].min()
    if column == 'population_density':
        nmax = nmax / 6
    fig = px.choropleth_map(unemp_c, geojson=geo_c, locations='lau', featureidkey="properties.lau", 
                         color=column, map_style="carto-positron", center = g_pars[cstr]['center'],
                         color_continuous_scale="sunset", zoom=g_pars[cstr]['zoom'],
                         range_color=(nmin, nmax), labels={column: lab_dict[column]}
                        )
    fig.update_layout(margin={"r":0,"t":25,"l":0,"b":0}, width=g_pars[cstr]['w'], height=g_pars[cstr]['h'])
    fig.update_traces(customdata=np.stack((unemp_c['name'],unemp_c[column]), axis=1), hovertemplate=(
        "<b>Region: %{customdata[0]}</b><br>"+\
        "Value: %{customdata[1]}"))
    return fig

def plot_uhist(cstr, rstr):
    c_hist = h_pars[cstr]
    r_hist = c_hist.filter(pl.col('lau') == rstr)
    r_hist = r_hist.with_columns((100 * pl.col('registered_unemployed') / pl.col('Y15-64')).alias('perc_unemp').round(2))
    r_hist = r_hist.sort(by='period')
    ugr = px.line(r_hist, x='period', y='perc_unemp', markers=False, width=900, height=450)
    ugr.update_xaxes({"tickvals": r_hist["period"].str.head(4), "tickangle": 45})
    return ugr
