import json
import geopandas as gp
import polars as pl
import plotly.express as px
import numpy as np

 
geo = json.load(open('public/converted_simp2.geojson','r'))

unemp = gp.read_file('public/converted_simp2.geojson', read_geometry=False)
unemp = unemp[['lau', 'name', 'registered_unemployed', 'Y15-64','population_density']]
unemp = pl.from_pandas(unemp)
unemp = unemp.with_columns((100 * pl.col('registered_unemployed') / pl.col('Y15-64')).alias('perc_unemp').round(2))

g_pars = {'SK': {'center': {"lon": 19.3, "lat": 48.7}, 'zoom': 6, 'w': 750, 'h': 400},
          'HU': {'center': {"lon": 19.5, "lat": 47.1}, 'zoom': 6, 'w': 780, 'h': 500},
          'PL': {'center': {"lon": 18.9, "lat": 51.9}, 'zoom': 5, 'w': 700, 'h': 500},
          'CZ': {'center': {"lon": 15.5, "lat": 49.7}, 'zoom': 6, 'w': 760, 'h': 500},
         }

def regions(cstr):
    c_regdf = unemp.filter(pl.col('lau').str.starts_with(cstr)).select(['name', 'lau'])
    c_regs = {k:v for k,v in zip(c_regdf['name'], c_regdf['lau'])}
    return c_regs
    
c_regions = {c: regions(c) for c in g_pars} 

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
    unemp_hist = pl.read_csv('public/lau1-history-iz.csv', 
    columns=["period", "lau", "name", "registered_unemployed",
             "registered_unemployed_females", "Y15-64", "Y15-64-females"])
    unemp_hist = unemp_hist.with_columns((100 * pl.col('registered_unemployed') / pl.col('Y15-64')).alias('perc_unemp').round(2))         
    unemp_hc = unemp_hist.filter(pl.col('lau').str.starts_with(cstr))
    return unemp_hc

h_pars = {k: get_country_unemp_history(k) for k in g_pars.keys()}


def get_country_pop_history(cstr):
    if not cstr in g_pars.keys():
        return   
    pop_hist = pl.read_csv('public/lau1-population-iz.csv', 
                            columns=["period", "lau", "name", "gender", "TOTAL"])
    pop_hc = pop_hist.filter(pl.col('lau').str.starts_with(cstr))
    return pop_hc


p_pars = {k: get_country_pop_history(k) for k in g_pars.keys()}
    

def plot_map(cstr, column='perc_unemp'):
    geo_c, unemp_c = u_pars[cstr]
    lab_dict = {'perc_unemp': 'Nezamestnanosť', 'population_density': 'Hustota'}
    nmax = 1.1 * unemp_c[column].max()
    nmin = 0.9 * unemp_c[column].min()
    if column == 'population_density':
        nmax = nmax / 6
    fig = px.choropleth_map(unemp_c, geojson=geo_c, locations='lau', featureidkey="properties.lau", 
                         color=column, map_style="carto-positron", center = g_pars[cstr]['center'],
                         color_continuous_scale="sunset", zoom=g_pars[cstr]['zoom'],
                         range_color=(nmin, nmax), labels={column: lab_dict[column]}
                        )
    width = g_pars[cstr]['w']
    if column == 'population_density':
        width = width - 25                     
    fig.update_layout(margin={"r":0,"t":25,"l":0,"b":0}, width=width, height=g_pars[cstr]['h'])
    fig.update_traces(customdata=np.stack((unemp_c['name'],unemp_c[column]), axis=1), hovertemplate=(
        "<b>Region: %{customdata[0]}</b><br>"+\
        "Hodnota: %{customdata[1]}"))
    return fig

def plot_uhist(cstr, rstr, kto):
    c_hist = h_pars[cstr]
    r_hist = c_hist.filter(pl.col('lau') == rstr)
    
    if kto == 'summary':
        r_hist = r_hist.sort(by='period')
        ugr = px.line(r_hist, x='period', y='perc_unemp', markers=False, 
                    labels={'perc_unemp': 'Nezamestnanosť %', 'period': 'Obdobie'},
                    width=900, height=450)
    else:                
        r_hist = r_hist.with_columns(ženy = (100 * pl.col('registered_unemployed_females') 
                                        / pl.col('Y15-64')).round(2))
        r_hist = r_hist.with_columns(muži = (pl.col('perc_unemp') - pl.col('ženy')).round(2))
        r_hist = r_hist.sort(by='period')
        if cstr == 'PL':
            r_hist = r_hist.filter(pl.col('registered_unemployed_females').is_not_null())
        r_hist = r_hist.sort(by='period')    
        ugr = px.line(r_hist, x='period', y=['muži', 'ženy'], markers=False, 
                      labels={'value': 'Nezamestnanosť %', 'period': 'Obdobie', 'variable': 'Premenná'},
                      width=900, height=450)
    ugr.update_xaxes({"tickvals": r_hist["period"].str.head(4), "tickangle": 45})
    ugr.update_layout(modebar_remove=['zoom', 'pan', 'lasso', 'select', 'toimage', ])
    return ugr


def plot_phist(cstr, rstr):
    p_hist = p_pars[cstr].sort(by='period')
    fem_df = p_hist.filter((pl.col('lau')==rstr) & (pl.col('gender') == 'females'))['period', 'TOTAL']\
                          .rename({'TOTAL': 'ženy'})
    if cstr != "HU":
        mal_df = p_hist.filter((pl.col('lau')==rstr) & (pl.col('gender') == 'males'))['period', 'TOTAL']\
                          .rename({'TOTAL': 'muži'})
        all_df = fem_df.join(mal_df, on='period').sort(by='period')
        all_df = all_df.with_columns((pl.col('muži') + pl.col('ženy')).alias('totcount'))
    else:
        tot_df = p_hist.filter((pl.col('lau')==rstr) & (pl.col('gender') == 'total'))['period', 'TOTAL']\
                          .rename({'TOTAL': 'totcount'})
        all_df = fem_df.join(tot_df, on='period').sort(by='period')
        all_df = all_df.with_columns((pl.col('totcount') - pl.col('ženy')).alias('muži'))    
    ugr = px.line(all_df, x='period', y=['muži', 'ženy'], markers=False, 
                  labels = {'period': 'Obdobie', 'value': 'Počet', 'variable': 'Premenná'},
                  width=900, height=450)
    return ugr #, all_df

def plot_veksklad(data_reg, year):
    r_data = data_reg[year].rename({'ages': 'Vek', 'males': "muži", 'femes': "ženy"})
    act_graph = px.line(r_data, x='Vek', y=['muži', 'ženy'], markers=False,
                        labels = {'value': 'Počet', 'variable': 'Premenná'},
                        width=900, height=450)
    return act_graph

def vek_anim(data_reg):
    lf = 20  # len(data_reg[1996]['ages']) napr.
    years, ages, males, females = [], [], [], []
    for year in data_reg.keys():
        dfy = data_reg[year]
        years.extend(lf * [year])
        ages.extend(dfy['ages'])
        males.extend(dfy['males'])
        females.extend(dfy['femes'])
    ylim = [0.98 * min(min(females), min(males)), 1.02 * max(max(females), max(males))]
    df_vek = pl.DataFrame({'Rok': years, 'Vek': ages, 'muži': males, 'ženy': females})
    gr_vek = px.bar(df_vek, x='Vek', y=['muži', 'ženy'], #markers=False, 
                    width=900, height=450, barmode='group',
                    animation_frame='Rok', labels = {'value': 'Počet', 'variable': 'Premenná'})
    gr_vek.add_vline(x=15)
    gr_vek.add_vline(x=64)                
    gr_vek.update_yaxes(range = ylim)                 
    return gr_vek
