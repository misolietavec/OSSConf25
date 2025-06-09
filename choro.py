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
    from funkcie import plot_map, plot_uhist, h_pars
    return h_pars, plot_map, plot_uhist


@app.cell
def _(mo):
    abbrev = {'Slovakia': 'SK', 'Poland': 'PL', 'Czechia': 'CZ', 'Hungary': 'HU'}
    countries_choice = mo.ui.dropdown(options=abbrev, value='Slovakia', label='Výber krajiny: ')
    valmap_choice = mo.ui.radio(options={'Unemployment (%)':'perc_unemp', 'Pop. density':'population_density'}, 
                                value='Unemployment (%)', inline=True, label='Value to plot: ')
    return countries_choice, valmap_choice


@app.cell
def _(countries_choice, mo, plot_map, valmap_choice):
    _cstr = countries_choice.value
    _vstr = valmap_choice.value
    _fig = plot_map(_cstr, _vstr)
    tab_map = mo.vstack([mo.md('<center><h3>Miera nezamestnanosti v percentách a hustota populácie</h3></center>'), countries_choice, valmap_choice, mo.ui.plotly(_fig)])
    return (tab_map,)


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
