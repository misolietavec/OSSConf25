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

__generated_with = "0.14.8"
app = marimo.App(
    width="medium",
    app_title="Slajdy OSSConf 25",
    layout_file="layouts/choro_slides.slides.json",
    sql_output="native",
)

with app.setup:
    import pickle

    from funkcie import plot_map, plot_uhist, c_regions, plot_phist, p_pars, plot_veksklad, vek_anim

    import marimo as mo


@app.cell
def _():
    logo = mo.image('public/ossconf.png').center()
    title = mo.md("""
    <h1>Vizualizácia dát o nezamestnanosti a populácii<br/><br/>
       v krajinách V4 v marimo notebooku. Slajdy.""")
    fullscreen = mo.md('Kliknite na malé modré Fullscreen vpravo dole&nbsp;').right()
    mo.vstack([logo, title, fullscreen], gap=5).center()
    return


@app.cell(hide_code=True)
def _():
    mo.md(
        r"""
    ## O dátach

    ### Sú to datasety M. Páleníka, ktoré  žijú [na zenodo.org](https://doi.org/10.5281/zenodo.6165135).
    ### Na horeuvedenej stránke sú aj popisy datasetov a počty údajov za krajiny V4.
    ### Poznámky: 
    - **hranice administratívnych jednotiek v geojson súbore príliš podrobné (musel som zjednodušiť, bez dier aby bolo)**
    - **rôzne časové rozpätia sledovanosti parametrov v jednotlivých krajinách**
    - **neúplné údaje (napr. vekové zloženie po 70-ke, v Poľsku)**
    - **nevhodný formát dát, hlavne u vekového zloženia (vekové kategórie skôr v riadkoch, ako v stĺpcoch)**
    """
    )
    return


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
    _regions = c_regions[countries_choice.value] #{k:v for k,v in zip(_c_regs['name'], _c_regs['lau'])}
    regions_choice = mo.ui.dropdown(options=_regions, allow_select_none=False, searchable=True, 
                                    value=list(_regions.keys())[0], label="Výber regiónu: ")
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
    _regions = c_regions['SK']

    sk_reg_choice = mo.ui.dropdown(options=_regions, allow_select_none=False, searchable=True, 
                                   value=list(_regions.keys())[0], label="Výber regiónu, SK: ")
    return sk_reg_choice, sk_unpic


@app.cell
def _(sk_reg_choice, sk_unpic):
    data_reg = sk_unpic[sk_reg_choice.value]
    return (data_reg,)


@app.cell(hide_code=True)
def _():
    mo.md(
        r"""
    ## Prečo marimo a nie jupyter?
    - **predovšetkým reaktivita - keď niečo zmením v jednej bunke, vykonajú sa všetky bunky na nej závisiace alebo sa označia ako "špinavé" pri lenivom spôsobe vykonávania**
    - **teda, ak zmeníme napr. hodnotu posuvníka v jednej bunke, všetky grafy, čo ho používajú, sa zmenia automaticky**
    - **predvídateľný spôsob vykonávania, "reproducibility"**
    - **formát NB je obyčajný Python zdroják, nie `json` ako v Jupyteri**
    - **vývoj aplikácie, samotná aplikácia, spôsob prezentácie (slajdy tieto) sa dejú v tom istom notebooku**
    - **pre priaznivcov AI: marimo editor má možnosť s AI pokecať a nechať jej generovať aj kód (zatiaľ nevyužívam)**
    - **rýchly vývoj, prudký nárast počtu vývojárov, ich otvorenosť k pripomienkam**

    ### Viac na [stránke marimo dokumentácie](https://docs.marimo.io/)
    """
    )
    return


@app.cell
def _():
    mo.vstack([mo.md('## Raketový štart'), mo.image('public/marimo.png')], gap=5)
    return


@app.cell(hide_code=True)
def _():
    mo.md(
        r"""
    ## K samotnému spracovaniu dát. Kód je v dvoch súboroch
    - ###**notebook `choro.py` (či ukecaná slajdová verzia `choro_slides.py`, v ktorej sme teraz), tu sa deje interaktivita**
    - ###**`funkcie.py` python súbor s funkciami na spracovanie dát a ich vizualizáciu. v tomto súbore sa nepoužíva `marimo`, iba moduly `polars, plotly, geopandas, numpy`**

    ### Dôsledok: **na interaktívnu aplikáciu môžeme použiť hocičo (`streamlit, plotly dash, panel, py-shiny, voilà, marimo`)**
    Tu sme sa pre `marimo` rozhodli. Pokus prepísať kód pre `Jupyter` a `panel` sa skončil znechutením, hoci pred dvomi rokmi...
    """
    )
    return


@app.cell
def _(countries_choice, regions_choice, valmap_choice, who_choice):
    _pokec = mo.md("## Pozrime sa na interaktívne prvky pre výber krajiny, regiónu, výberu zobrazenia na mape a v grafe")
    _doslov = mo.md("""### Výber regiónu závisí od výberu krajiny a zobrazenie grafu závisí od výberu regiónu. Pomeňme niečo a potom sa pozrime na výslednú aplikáciu, ktorá je na konci tohto NB (posledný slajd). A nazad.
    ### Vidíme, že hodnota výberu v tých istých grafických prvkoch je rovnaká v celom NB, v každej bunke. """)
    mo.vstack([_pokec, mo.hstack([countries_choice, regions_choice, valmap_choice, who_choice]), _doslov ],gap=3)
    return


@app.cell(hide_code=True)
def _():
    mo.md(
        r"""
    ## Ukážka kódu pre zobrazenie histórie nezamestnanosti.
    ```python
    import marimo as mo
    from funkcie import plot_uhist, c_regions

    # definícia grafických prvkov pre výber krajiny a zobrazenie podľa pohlaví
    _abbrev = {'Slovensko': 'SK', 'Poľsko': 'PL', 'Česko': 'CZ', 'Maďarsko': 'HU'}
    countries_choice = mo.ui.dropdown(options=_abbrev, value='Slovensko', label='Výber krajiny: ')
    who_choice = mo.ui.radio(options={'Celkovo':'summary', 'Ženy, muži':'bygender'}, value='Celkovo')

    # v inej bunke - definícia UI výberu regiónov - prečo?
    _regions = c_regions[countries_choice.value]
    regions_choice = mo.ui.dropdown(options=_regions, allow_select_none=False, searchable=True, 
                                    value=list(_regions.keys())[0], label="Výber regiónu: ")

    # v inej bunke, funkcia plot_uhist má takúto hlavičku: def plot_uhist(cstr, rstr, kto)
    # v NB sa za tie parametre dosadia hodnoty UI prvkov a to je všetko 
    _r_hist = plot_uhist(countries_choice.value, regions_choice.value, who_choice.value)
    _nadpis = mo.md(f'<center><h3>História nezamestnanosti</h3></center>')
    tab_history = mo.vstack([_nadpis, mo.hstack([countries_choice, regions_choice, who_choice],justify='center', gap=5), _r_hist])
    ```
    """
    )
    return


@app.cell
def _(tab_history):
    mo.vstack([mo.md('## Tu je výsledok, interaktívne zobrazenie histórie nezamestnanosti').center(), tab_history])
    return


@app.cell
def _():
    zaver = mo.md(
        r"""
    #Záver
    ### Zdrojáky nájdete na githube [https://github.com/misolietavec/OSSConf25](https://github.com/misolietavec/OSSConf25)
    ### Kód sa dá zlepšiť - zjednodušením, doplnením vizualizácie a štatistického vyhodnotenia...
    ### Keby ste ekvivalentnú aplikáciu vytvorili v inom interaktívnom prostredi, bomba by bola
    ### V priebehu konferencie, kto chce podrobnejšíe info o `marimo` a tejto aplikácii, môžeme sadnúť a pokecať.
    ### Ak napíšete na _mike@feelmath.eu_ môžeme dohodnúť debatu napr. formou videokonfery na [Jitsi meet](meet.jit.si)
    ### To bude ako **permanentný workshop** pre tých, čo sa rozhodli `marimo` vyskúšať nie jednorázovo.
    ### V každom NB v nastaveniach (položka `Resources`) sú odkazy na dokumentáciu a sociálne siete aktívnej marimo komunity.""").center()
    koniec = mo.md("<center><h2>That's all, folks.</h2></center>").center()
    mo.vstack([zaver, koniec])
    return


@app.cell
def _(data_reg, sk_reg_choice):
    _p_plot = mo.ui.plotly(vek_anim(data_reg))
    _nadpis = mo.md('''### Veková skladba obyvateľstva Slovenska
                    #### Zvislé čiary - ohraničenie produktívneho veku''')
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
        ## Výsledná aplikácia
        ### Aktuálne dáta po regiónoch, história nezamestnanosti, vývoj populácie, veková skladba.
        #### Zdrojáky aplikácie nájdete [na githube](https://github.com/misolietavec/OSSConf25)
        """
    )
    return (nadpis,)


@app.cell
def _(nadpis, tabs):
    app = mo.vstack([nadpis, tabs], gap=2.5)
    app
    return


if __name__ == "__main__":
    app.run()
