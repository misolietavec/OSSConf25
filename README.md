## Marimo notebooks for visualising unemployment dataset in V4 countries
 
This is the repository of materials for the contribution at OSSConf 2025 in
Žilina, Slovakia. 

We use the open datasets from [LAU1 dataset](https://zenodo.org/records/14242424) for
visualising unemployment and population data in regions of V4 countries.

There are two marimo notebooks:
- ```choro.py``` maps and line graphs for LAU1 datasets
- ```choro_all.py``` version of ```choro.py``` for webassambly

and the python file ```funkcie.py ``` with several helper functions used in notebooks.

Also the needed datasets are included.

For editing and running notebooks you should use virtual environment with installed packages ```marimo, uv```.

Edit notebook:  
```marimo edit --sandbox choro.py```

Run notebook:
```marimo run --sandbox choro.py``` (dependencies will be automatically installed in isolated environment).

The web application (running choro.py in read-only mode) can be accessed at
[feelmath.eu server](https://unemp.feelmath.eu/). 
