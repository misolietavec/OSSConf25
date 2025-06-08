# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "altair==5.5.0",
#     "geojson==3.2.0",
#     "geopandas==1.1.0",
#     "marimo",
#     "numpy==2.2.6",
#     "plotly==6.1.2",
#     "polars==1.30.0",
#     "pyarrow==20.0.0",
# ]
# ///

import marimo

__generated_with = "0.13.15"
app = marimo.App(
    width="medium",
    app_title="Mapy nezamestnanosti",
    sql_output="native",
)


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _():
    import json
    import geopandas as gp
    import polars as pl
    import plotly.express as px
    import numpy as np
    return gp, json, np, pl, px


@app.cell
def _(gp, json, pl):
    abbrev = {'Slovakia': 'SK', 'Poland': 'PL', 'Czechia': 'CZ', 'Hungary': 'HU'}

    geo = json.load(open('converted_simp2.geojson','r'))

    unemp = gp.read_file('converted_simp2.geojson', read_geometry=False)
    unemp = unemp[['lau', 'name', 'registered_unemployed', 'Y15-64']]
    unemp = pl.from_pandas(unemp)
    unemp = unemp.with_columns((100 * pl.col('registered_unemployed') / pl.col('Y15-64')).alias('perc_unemp').round(2))

    g_pars = {'SK': {'center': {"lon": 19.3, "lat": 48.7}, 'zoom': 6, 'w': 750, 'h': 400},
              'HU': {'center': {"lon": 19.3, "lat": 47.1}, 'zoom': 6, 'w': 750, 'h': 500},
              'PL': {'center': {"lon": 18.9, "lat": 51.9}, 'zoom': 5, 'w': 700, 'h': 500},
              'CZ': {'center': {"lon": 15.9, "lat": 49.7}, 'zoom': 6, 'w': 750, 'h': 500},
             }
    return abbrev, g_pars, geo, unemp


@app.cell
def _():
    return


@app.cell
def _(g_pars, geo, pl, unemp):
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
    return get_country_unemp_history, u_pars


@app.cell
def _(g_pars, get_country_unemp_history, np, pl, px, u_pars):
    h_pars = {k: get_country_unemp_history(k) for k in g_pars.keys()}
    
    def plot_map(cstr):
        geo_c, unemp_c = u_pars[cstr]
        nmax = 1.1 * unemp_c['perc_unemp'].max()
        fig = px.choropleth_map(unemp_c, geojson=geo_c, locations='lau', featureidkey="properties.lau", 
                             color='perc_unemp', map_style="carto-positron", center = g_pars[cstr]['center'],
                             color_continuous_scale="sunset", zoom=g_pars[cstr]['zoom'],
                             range_color=(0, nmax), labels={'perc_unemp': 'Nezam. %'}
                            )
        fig.update_layout(margin={"r":0,"t":25,"l":0,"b":0}, width=g_pars[cstr]['w'], height=g_pars[cstr]['h'])
        fig.update_traces(customdata=np.stack((unemp_c['name'],unemp_c['perc_unemp']), axis=1), hovertemplate=(
            "<b>Region: %{customdata[0]}</b><br>"+\
            "Perc. of unemployment: %{customdata[1]}"))
        return fig

    def plot_uhist(cstr, rstr):
        c_hist = h_pars[cstr]
        r_hist = c_hist.filter(pl.col('lau') == rstr)
        r_hist = r_hist.with_columns((100 * pl.col('registered_unemployed') / pl.col('Y15-64')).alias('perc_unemp').round(2))
        r_hist = r_hist.sort(by='period')
        ugr = px.line(r_hist, x='period', y='perc_unemp', markers=False, width=900, height=450)
        ugr.update_xaxes({"tickvals": r_hist["period"].str.head(4), "tickangle": 45})
        return ugr
    return h_pars, plot_map, plot_uhist


@app.cell
def _(countries_choice, mo, plot_map):
    _cstr = countries_choice.value
    _fig = plot_map(_cstr)
    tab_map = mo.vstack([mo.md('<center><h3>Miera nezamestnanosti v percentách</h3></center>'), countries_choice, mo.ui.plotly(_fig)])
    return (tab_map,)


@app.cell
def _(abbrev, mo):
    countries_choice = mo.ui.dropdown(options=abbrev, value='Slovakia', label='Výber krajiny: ')
    return (countries_choice,)


@app.cell
def _(countries_choice, h_pars, mo):
    _c_regs = h_pars[countries_choice.value]
    _regions = {k:v for k,v in zip(_c_regs['name'], _c_regs['lau'])}
    regions_choice = mo.ui.dropdown(options=_regions, allow_select_none=False, searchable=True, 
                                    value=_c_regs['name'][0], label="Výber regiónu: ") 
    return (regions_choice,)


@app.cell
def _(countries_choice, mo, plot_uhist, regions_choice):
    _r_hist = plot_uhist(countries_choice.value, regions_choice.value)
    _nadpis = mo.md(f'<center><h3>História nezamestnanosti</h3></center>')
    tab_history = mo.vstack([_nadpis, mo.hstack([countries_choice, regions_choice],justify='center', gap=5), _r_hist])
    return (tab_history,)


@app.cell
def _(mo, tab_history, tab_map):
    tabs = mo.ui.tabs({"Nezamestnanosť na mape": tab_map, "História po regiónoch": tab_history}, lazy=True)
    return (tabs,)


@app.cell
def _(mo):
    nadpis = mo.md(
        """
        ## Nezamestnanosť v krajinách V4
        ### Aktuálne dáta po regiónoch, história nezamestnanosti, vývoj populácie.
        """
    )
    return (nadpis,)


@app.cell
def _(mo, nadpis, tabs):
    app = mo.vstack([nadpis, tabs])
    app
    return


if __name__ == "__main__":
    app.run()
