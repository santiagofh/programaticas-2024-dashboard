# %%
import pandas as pd
import os
from glob import glob
# %%
path_nac_2022=r"C:\Users\fariass\OneDrive - SUBSECRETARIA DE SALUD PUBLICA\Escritorio\DATA\NACIMIENTO\2022\NAC2022.csv"
path_nac_2023=r"C:\Users\fariass\OneDrive - SUBSECRETARIA DE SALUD PUBLICA\Escritorio\DATA\NACIMIENTO\2023\NAC2023.csv"
path_nac_2024=r"C:\Users\fariass\OneDrive - SUBSECRETARIA DE SALUD PUBLICA\Escritorio\DATA\NACIMIENTO\2024\NAC2024.csv"
path_nac_2025=r"C:\Users\fariass\OneDrive - SUBSECRETARIA DE SALUD PUBLICA\Escritorio\DATA\NACIMIENTO\2025\NAC2025.csv"
# %%
nac_2022=pd.read_csv(path_nac_2022,encoding="LATIN1",sep=";", nrows=100)
#%%
# nac_2023=pd.read_csv(path_nac_2023,encoding="LATIN1",sep=";")
# nac_2024=pd.read_csv(path_nac_2024,encoding="LATIN1",sep=";")
# nac_2025=pd.read_csv(path_nac_2025,encoding="LATIN1",sep=";")
# %%
