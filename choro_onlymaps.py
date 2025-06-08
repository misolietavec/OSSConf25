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
def _(countries_choice, geo, pl, unemp):
    def get_countries_mapdata(clist):
        gf = geo['features']
        geo_cf = [p for p in gf if p['properties']['lau'][:2] in clist]
        geo_c = {'type': 'FeatureCollection', 'name': f'Krajiny V4', 'features': geo_cf}
        unemp_c = unemp.filter(pl.col('lau').str.contains_any(countries_choice.value))
        return geo_c, unemp_c
    return (get_countries_mapdata,)


@app.cell
def _(g_pars, get_countries_mapdata, np, px):
    def plot_map(clist):
        geo_c, unemp_c = get_countries_mapdata(clist)
        nmax = 1.1 * unemp_c['perc_unemp'].max()
        lon = np.mean([g_pars[cstr]['center']['lon'] for cstr in clist])
        lat = np.mean([g_pars[cstr]['center']['lat'] for cstr in clist])
        fig = px.choropleth_map(unemp_c, geojson=geo_c, locations='lau', featureidkey="properties.lau", 
                             color='perc_unemp', map_style="carto-positron", # center = {"lon": lon, "lat": lat},
                             color_continuous_scale="sunset", zoom=6, center ={"lon": 17.4, "lat": lat}, 
                             range_color=(0, nmax), labels={'perc_unemp': 'Nezam. %'}
                            )
        fig.update_layout(margin={"r":0,"t":25,"l":0,"b":0}, width=1100, height=900)
        fig.update_traces(customdata=np.stack((unemp_c['name'],unemp_c['perc_unemp']), axis=1), hovertemplate=(
            "<b>Region: %{customdata[0]}</b><br>"+\
            "Perc. of unemployment: %{customdata[1]}"))
        return fig
    return (plot_map,)


@app.cell
def _(countries_choice, mo, plot_map):
    _clist = countries_choice.value
    _fig = plot_map(_clist)
    maps = mo.vstack([mo.md('<center><h3>Miera nezamestnanosti v percentách</h3></center>'), countries_choice, mo.ui.plotly(_fig)])
    return (maps,)


@app.cell
def _(abbrev, mo):
    countries_choice = mo.ui.multiselect(options=abbrev, value=['Slovakia', 'Czechia'], label='Výber krajín: ')
    return (countries_choice,)


@app.cell
def _(maps):
    app = maps
    app
    return


if __name__ == "__main__":
    app.run()
