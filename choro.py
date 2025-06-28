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

__generated_with = "0.14.6"
app = marimo.App(
    width="medium",
    app_title="Nezamestnanosť V4",
    sql_output="native",
)

with app.setup:
    import locale
    import pickle
    from funkcie import plot_map, plot_uhist, h_pars, plot_phist, p_pars, plot_veksklad, vek_anim
    import plotly.express as px

    import marimo as mo


@app.cell
def _():
    _abbrev = {'Slovensko': 'SK', 'Poľsko': 'PL', 'Česko': 'CZ', 'Maďarsko': 'HU'}
    countries_choice = mo.ui.dropdown(options=_abbrev, value='Slovensko', label='Výber krajiny: ')
    valmap_choice = mo.ui.radio(options={'Nezamestnanosť (%)':'perc_unemp', 'Hustota obyvateľstva':'population_density'}, 
                                value='Nezamestnanosť (%)', inline=True, label='Premenná: ')
    return countries_choice, valmap_choice


@app.cell
def _(countries_choice, valmap_choice):
    _cstr = countries_choice.value
    _vstr = valmap_choice.value
    _fig = plot_map(_cstr, _vstr)
    tab_map = mo.vstack([mo.md('<center><h3>Miera nezamestnanosti v percentách a hustota populácie</h3></center>'), countries_choice, valmap_choice, mo.ui.plotly(_fig)])
    return (tab_map,)


@app.cell
def _(countries_choice):
    _c_regs = h_pars[countries_choice.value]
    _regions = {k:v for k,v in zip(_c_regs['name'], _c_regs['lau'])}
    regions_choice = mo.ui.dropdown(options=_regions, allow_select_none=False, searchable=True, 
                                    value=_c_regs['name'][0], label="Výber regiónu: ")
    who_choice = mo.ui.radio(options={'Celkovo':'summary', 'Ženy, muži':'bygender'}, value='Celkovo')
    return regions_choice, who_choice


@app.cell
def _(countries_choice, regions_choice, who_choice):
    _r_hist = plot_uhist(countries_choice.value, regions_choice.value, who_choice.value)
    _nadpis = mo.md(f'<center><h3>História nezamestnanosti</h3></center>')
    tab_history = mo.vstack([_nadpis, mo.hstack([countries_choice, regions_choice, who_choice],justify='center', gap=5), _r_hist])
    return (tab_history,)


@app.cell
def _(countries_choice, regions_choice):
    _p_hist = plot_phist(countries_choice.value, regions_choice.value)
    _nadpis = mo.md(f'<center><h3>Vývoj populácie</h3></center>')
    tab_pop = mo.vstack([_nadpis, mo.hstack([countries_choice, regions_choice], justify='center', gap=5), _p_hist])
    return (tab_pop,)


@app.cell
def _():
    sk_unpic = pickle.load(open('public/sk_data.pickle','rb'))
    _c_regs = h_pars['SK']
    _regions = {k:v for k,v in zip(_c_regs['name'], _c_regs['lau'])}
    sk_reg_choice = mo.ui.dropdown(options=_regions, allow_select_none=False, searchable=True, value=_c_regs['name'][0], label="Výber regiónu, SK: ")
    return sk_reg_choice, sk_unpic


@app.cell
def _(sk_reg_choice, sk_unpic):
    data_reg = sk_unpic[sk_reg_choice.value]
    return (data_reg,)


@app.cell
def _(data_reg, sk_reg_choice):
    _p_plot = mo.ui.plotly(vek_anim(data_reg))
    _nadpis = mo.md('''### Veková skladba obyvateľstva Slovenska
                    #### Zvislé čiary - ohraničenie produktívneho veku''')
    # _nadpis = mo.Html(f'<center>{_nadpis}</center>')
    tab_veksklad = mo.vstack([mo.hstack([_nadpis, sk_reg_choice], justify='start', gap=15), _p_plot])
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
