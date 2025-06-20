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

__generated_with = "0.14.0"
app = marimo.App(
    width="medium",
    app_title="Nezamestnanosť V4",
    sql_output="native",
)

with app.setup:
    import locale
    import pickle
    import plotly.express as px

    import marimo as mo


@app.cell
def _():
    # from funkcie import plot_map, plot_uhist, h_pars, plot_phist, p_pars, plot_veksklad
    import json
    import geopandas as gp
    import polars as pl
    import numpy as np

    data_path = str(mo.notebook_location() / "public") 
    data_path
    return data_path, gp, json, np, pl


@app.cell
def _(data_path, gp, json, np, pl):
    geo = json.load(open(str(mo.notebook_location() / "public" / "converted_simp2.geojson"),'r'))

    unemp = gp.read_file(f'{data_path}/converted_simp2.geojson', read_geometry=False)
    unemp = unemp[['lau', 'name', 'registered_unemployed', 'Y15-64','population_density']]
    unemp = pl.from_pandas(unemp)
    unemp = unemp.with_columns((100 * pl.col('registered_unemployed') / pl.col('Y15-64')).alias('perc_unemp').round(2))

    g_pars = {'SK': {'center': {"lon": 19.3, "lat": 48.7}, 'zoom': 6, 'w': 750, 'h': 400},
              'HU': {'center': {"lon": 19.5, "lat": 47.1}, 'zoom': 6, 'w': 780, 'h': 500},
              'PL': {'center': {"lon": 18.9, "lat": 51.9}, 'zoom': 5, 'w': 700, 'h': 500},
              'CZ': {'center': {"lon": 15.5, "lat": 49.7}, 'zoom': 6, 'w': 760, 'h': 500},
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
        unemp_hist = pl.read_csv(f'{data_path}/lau1-history-iz.csv', 
        columns=["period", "lau", "name", "registered_unemployed",
                 "registered_unemployed_females", "Y15-64", "Y15-64-females"])
        unemp_hist = unemp_hist.with_columns((100 * pl.col('registered_unemployed') / pl.col('Y15-64')).alias('perc_unemp').round(2))         
        unemp_hc = unemp_hist.filter(pl.col('lau').str.starts_with(cstr))
        return unemp_hc

    h_pars = {k: get_country_unemp_history(k) for k in g_pars.keys()}


    def get_country_pop_history(cstr):
        if not cstr in g_pars.keys():
            return   
        pop_hist = pl.read_csv(f'{data_path}/lau1-population-iz.csv', 
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
        return ugr, all_df

    def plot_veksklad(data_reg, year):
        r_data = data_reg[year].rename({'ages': 'Vek', 'males': "muži", 'femes': "ženy"})
        act_graph = px.line(r_data, x='Vek', y=['muži', 'ženy'], markers=False,
                            labels = {'value': 'Počet', 'variable': 'Premenná'},
                            width=900, height=450)
        return act_graph

    return h_pars, plot_map, plot_phist, plot_uhist, plot_veksklad


@app.cell
def _():
    abbrev = {'Slovensko': 'SK', 'Poľsko': 'PL', 'Česko': 'CZ', 'Maďarsko': 'HU'}
    countries_choice = mo.ui.dropdown(options=abbrev, value='Slovensko', label='Výber krajiny: ')
    valmap_choice = mo.ui.radio(options={'Nezamestnanosť (%)':'perc_unemp', 'Hustota obyvateľstva':'population_density'}, 
                                value='Nezamestnanosť (%)', inline=True, label='Premenná: ')
    return countries_choice, valmap_choice


@app.cell
def _(countries_choice, plot_map, valmap_choice):
    _cstr = countries_choice.value
    _vstr = valmap_choice.value
    _fig = plot_map(_cstr, _vstr)
    tab_map = mo.vstack([mo.md('<center><h3>Miera nezamestnanosti v percentách a hustota populácie</h3></center>'), countries_choice, valmap_choice, mo.ui.plotly(_fig)])
    return (tab_map,)


@app.cell
def _(countries_choice, h_pars):
    _c_regs = h_pars[countries_choice.value]
    _regions = {k:v for k,v in zip(_c_regs['name'], _c_regs['lau'])}
    regions_choice = mo.ui.dropdown(options=_regions, allow_select_none=False, searchable=True, 
                                    value=_c_regs['name'][0], label="Výber regiónu: ")
    who_choice = mo.ui.radio(options={'Celkovo':'summary', 'Ženy, muži':'bygender'}, value='Celkovo')
    return regions_choice, who_choice


@app.cell
def _(countries_choice, plot_uhist, regions_choice, who_choice):
    _r_hist = plot_uhist(countries_choice.value, regions_choice.value, who_choice.value)
    _nadpis = mo.md(f'<center><h3>História nezamestnanosti</h3></center>')
    tab_history = mo.vstack([_nadpis, mo.hstack([countries_choice, regions_choice, who_choice],justify='center', gap=5), _r_hist])
    return (tab_history,)


@app.cell
def _(countries_choice, plot_phist, regions_choice):
    _p_hist, _all_df = plot_phist(countries_choice.value, regions_choice.value)
    _nadpis = mo.md(f'<center><h3>Vývoj populácie</h3></center>')
    tab_pop = mo.vstack([_nadpis, mo.hstack([countries_choice, regions_choice], justify='center', gap=5), _p_hist])
    return (tab_pop,)


@app.cell
def _(data_path, h_pars):
    sk_unpic = pickle.load(open(f'{data_path}/sk_data.pickle','rb'))
    _c_regs = h_pars['SK']
    _regions = {k:v for k,v in zip(_c_regs['name'], _c_regs['lau'])}
    sk_reg_choice = mo.ui.dropdown(options=_regions, allow_select_none=False, searchable=True, value=_c_regs['name'][0], label="Výber regiónu, SK: ")
    return sk_reg_choice, sk_unpic


@app.cell
def _(sk_reg_choice, sk_unpic):
    data_reg = sk_unpic[sk_reg_choice.value]
    years = sorted(list(data_reg.keys()))
    reg_slider = mo.ui.slider(start=years[0], stop=years[-1], step=1, label='Rok: ', show_value=False, value=years[0])
    return data_reg, reg_slider


@app.cell
def _(data_reg, plot_veksklad, reg_slider, sk_reg_choice):
    _reg_valstr = mo.md(f" {reg_slider.value}")
    p_plot = plot_veksklad(data_reg, reg_slider.value)
    _nadpis = mo.md(f'<center><h3>Veková skladba obyvateľstva Slovenska</h3></center>')
    tab_veksklad = mo.vstack([_nadpis, mo.hstack([sk_reg_choice, reg_slider, _reg_valstr],justify='center', gap=5), p_plot])
    return (tab_veksklad,)


@app.cell
def _(tab_history, tab_map, tab_pop, tab_veksklad):
    tabs = mo.ui.tabs({"Nezamestnanosť na mape": tab_map, "História po regiónoch": tab_history, 
                       'Demografický vývoj po regiónoch': tab_pop, "Veková skladba, regiony SK": tab_veksklad})
    return (tabs,)


@app.cell
def _():
    nadpis = mo.md(
        """
        ## Nezamestnanosť v krajinách V4
        ### Aktuálne dáta po regiónoch, história nezamestnanosti, vývoj populácie, veková skladba.
        #### Zdrojáky aplikácie nájdete [na githube](https://github.com/misolietavec/OSSConf25)
        """
    )
    return (nadpis,)


@app.cell
def _(nadpis, tabs):
    app = mo.vstack([nadpis, tabs],gap=2.5)
    app
    return


if __name__ == "__main__":
    app.run()
