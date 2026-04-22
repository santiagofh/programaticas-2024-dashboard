# Metodología para el Cálculo de Coberturas de Vacunas Programáticas
**Región Metropolitana — Año evaluado: 2024**  
**Fuente metodológica:** DEIS v2.0 (Dic-2025)  
**Scripts:** `1_numerador_rni_vacunas_2024.py` · `2_denominadores_2024.py` · `3_calcular_coberturas_2024.py`

---

## Índice
1. [Resumen del flujo](#1-resumen-del-flujo)
2. [Fuentes de datos](#2-fuentes-de-datos)
3. [Fórmula general](#3-fórmula-general)
4. [Script 1 — Numerador (RNI)](#4-script-1--numerador-rni)
5. [Script 2 — Denominadores](#5-script-2--denominadores)
6. [Script 3 — Cálculo de coberturas](#6-script-3--cálculo-de-coberturas)
7. [Detalle por vacuna](#7-detalle-por-vacuna)
8. [Notas metodológicas importantes](#8-notas-metodológicas-importantes)
9. [Alertas y pendientes](#9-alertas-y-pendientes)

---

## 1. Resumen del flujo

```
RNI (t, t+1, t+2)   →  1_numerador      →  output/numerador_rni_2024.csv
SRCeI + INE + Mineduc →  2_denominadores  →  output/denominador_nacimientos_2024.csv
                                             output/denominador_neumococica_65_2024.csv
                                             output/denominador_matricula_escolar_2024.csv
Numerador + Denominadores → 3_coberturas  →  output/coberturas_vacunas_2024.csv / .xlsx
```

**Orden de ejecución:**
```bash
python 1_numerador_rni_vacunas_2024.py
python 2_denominadores_2024.py
python 3_calcular_coberturas_2024.py
```

---

## 2. Fuentes de datos

| Fuente | Datos | Usado en |
|--------|-------|----------|
| **RNI** (Registro Nacional de Inmunizaciones) | Vacunas administradas 2024–2026 | Script 1 |
| **SRCeI** (Registro Civil) | Nacidos vivos inscritos 2021–2024 | Script 2 — nacimientos |
| **INE** Proyecciones 2002–2035 por comuna | Población 65 años 2024 | Script 2 — personas mayores |
| **Mineduc** Matrícula por Curso 2024 | Matrícula 1°, 4°, 5°, 8° básico RM | Script 2 — escolar |

**Rutas de archivos (configurar en cada script):**
```
DATA/RNI/PROGRAMATICAS/2024–2026/          → Script 1
DATA/NACIMIENTO/2021–2024/NAC<año>.csv     → Script 2
data/estimaciones-y-proyecciones-...csv    → Script 2
data/20241003_Resumen_Matrícula_Curso_...  → Script 2
```

---

## 3. Fórmula general

### Vacunas infantiles y personas mayores
```
Cobertura (%) = (Vacunados año t + t+1 + t+2  [nacidos cohorte t]) 
                ─────────────────────────────────────────────────── × 100
                       Población objetivo cohorte año t
```

- **Numerador:** vacunados de la cohorte del año evaluado (t), incluyendo los que se vacunaron en t+1 y t+2
- **Denominador:** nacidos vivos inscritos (SRCeI) o proyección INE según vacuna

### Vacunas escolares
```
Cobertura (%) = Vacunados año t que cursan X° básico
                ────────────────────────────────────── × 100
                   Matriculados en X° básico año t
```

- **Numerador:** vacunados según **establecimiento de salud** (comuna de **ocurrencia**)
- **Denominador:** matrícula Mineduc según **comuna del colegio**

### Gestantes
```
Cobertura (%) = Gestantes vacunadas ≥ 28 sem durante año t
                ─────────────────────────────────────────── × 100
                    Estimación de gestantes año t (Prophet)
```

---

## 4. Script 1 — Numerador (RNI)

### Filtros aplicados al RNI
```python
COD_COMUNA_RESID entre 13000–13999   # Solo RM
VACUNA_ADMINISTRADA == "SI"
REGISTRO_ELIMINADO == "NO"
CRITERIO_ELEGIBILIDAD != "EPRO"
DOSIS no contiene "EPRO"
FECHA_INMUNIZACION.year in [2024, 2025, 2026]   # años t, t+1, t+2
```

### Lógica de join (columna COD_COMUNA_JOIN)
- **Vacunas regulares** → `COD_COMUNA_RESID` (residencia del vacunado)
- **Vacunas escolares** → `COD_COMUNA_OCURR` (comuna donde ocurrió la vacunación)

### Ventanas de cohorte por vacuna

| Clave | Ventana nacimiento | Vacunas |
|-------|--------------------|---------|
| `BCG_RN` | Ene–Dic 2024 | BCG |
| `HepB_RN` | Ene–Dic 2024 | Hepatitis B RN |
| `Cohorte_2M` | Nov 2023 – Oct 2024 | Hexavalente 1°, Neumocócica Conj 1°, Meningocócica Recomb 1° |
| `Cohorte_4M` | Sep 2023 – Ago 2024 | Hexavalente 2°, Neumocócica Conj 2°, Meningocócica Recomb 2° |
| `Hexavalente_3d_6m` | Jul 2023 – Jun 2024 | Hexavalente 3° |
| `Cohorte_12M` | Ene–Dic 2023 | SRP 1°, Neumocócica Conj Ref, Meningocócica Conj |
| `Cohorte_18M` | Jul 2022 – Jun 2023 | Varicela 1°, Hepatitis A, Meningocócica Recomb Ref |
| `Hexavalente_ref_18m` | Jul 2022 – Jun 2023 | Hexavalente Refuerzo |
| `Cohorte_36M` | Ene–Dic 2021 | SRP 2°, Varicela 2° |
| `Neumococica_Polisacarida_65` | Nacidos año 1959 | Neumocócica Polisacárida |
| `dTpa_1basico` | Jul 2016 – Jun 2018 | dTpa 1° básico |
| `dTpa_8basico` | Jul 2009 – Jun 2011 | dTpa 8° básico |
| `VPH_4basico` | Ene 2014 – Jun 2015 | VPH 4° básico (DOSIS_UNICA + 1RA_DOSIS) |
| `VPH_5basico` | Ene 2013 – Jun 2014 | VPH 5° básico (2DA_DOSIS, solo 2024) |
| `dTpa_Gestantes` | Nacidas 1975–2008 | dTpa gestantes |

### Columnas del output
```
COD_COMUNA_JOIN      → clave para join con denominador
COD_COMUNA_RESID     → residencia del vacunado
COMUNA_RESIDENCIA    → nombre comuna residencia
VACUNA_DASHBOARD     → nombre vacuna estandarizado
CLAVE_DENOMINADOR    → clave para cruzar con denominador
VACUNAS_ADMINISTRADAS
```

---

## 5. Script 2 — Denominadores

Genera **3 archivos** en una sola ejecución:

### A) `denominador_nacimientos_2024.csv`
- **Fuente:** SRCeI (Nacidos Vivos Inscritos)
- **Años cargados:** 2021, 2022, 2023, 2024
- **Filtro:** COMUNA_N entre 13000–13999 (RM)
- **Estructura:** una columna por cohorte, una fila por comuna

### B) `denominador_neumococica_65_2024.csv`
- **Fuente:** Proyecciones INE 2002–2035 por comuna
- **Filtro:** Región 13, Edad = 65, año 2024
- **Suma:** ambos sexos por comuna
- **Columna:** `Neumococica_Polisacarida_65`

### C) `denominador_matricula_escolar_2024.csv`
- **Fuente:** Mineduc — Resumen Matrícula por Curso 2024
- **Filtros:** COD_REG_RBD = 13, COD_ENSE = 110 (básica regular), ESTADO_ESTAB = 1, COD_GRADO ∈ {1, 4, 5, 8}
- **Columnas:** `dTpa_1basico`, `VPH_4basico`, `VPH_5basico`, `dTpa_8basico`

> **Pendiente:** `denominador_gestantes_2024.csv` — requiere modelo Prophet con serie histórica de nacidos vivos 1990–2023

---

## 6. Script 3 — Cálculo de coberturas

### Lógica de join
```python
coberturas = numerador.merge(
    denominador_long,
    left_on  = ["COD_COMUNA_JOIN", "CLAVE_DEN"],
    right_on = ["COMUNA_N",        "CLAVE_DEN"],
)
```

El denominador unificado (`denominador_long`) apila en formato long:
1. Nacimientos → melt de wide a long
2. INE 65 años → asigna `CLAVE_DEN = "Neumococica_Polisacarida_65"`
3. Matrícula escolar → melt de wide a long
4. Gestantes → si existe el archivo, agrega `CLAVE_DEN = "dTpa_Gestantes"`

### Resumen regional
El resumen regional obtiene el denominador **directamente de `denominador_long`** (suma única por clave), evitando duplicación por el join escolar.

### Outputs
- `coberturas_vacunas_2024.csv` — detalle por comuna y vacuna
- `coberturas_vacunas_2024.xlsx` — dos pestañas: `Por_Comuna` / `Resumen_Regional`

---

## 7. Detalle por vacuna

| Vacuna | Esquema | Denominador | Fuente denominador |
|--------|---------|-------------|-------------------|
| BCG | Dosis única (RN) | NV Ene–Dic 2024 | SRCeI |
| Hepatitis B RN | Dosis única (RN) | NV Ene–Dic 2024 | SRCeI |
| Hexavalente 1° | 2 meses | NV Nov 2023–Oct 2024 | SRCeI |
| Hexavalente 2° | 4 meses | NV Sep 2023–Ago 2024 | SRCeI |
| Hexavalente 3° | 6 meses | NV Jul 2023–Jun 2024 | SRCeI |
| Hexavalente Refuerzo | 18 meses | NV Jul 2022–Jun 2023 | SRCeI |
| Neumocócica Conjugada 1° | 2 meses | NV Nov 2023–Oct 2024 | SRCeI |
| Neumocócica Conjugada 2° | 4 meses | NV Sep 2023–Ago 2024 | SRCeI |
| Neumocócica Conjugada Refuerzo | 12 meses | NV Ene–Dic 2023 | SRCeI |
| Meningocócica Recombinante 1° | 2 meses | NV Nov 2023–Oct 2024 | SRCeI |
| Meningocócica Recombinante 2° | 4 meses | NV Sep 2023–Ago 2024 | SRCeI |
| Meningocócica Recombinante Refuerzo | 18 meses | NV Jul 2022–Jun 2023 | SRCeI |
| Meningocócica Conjugada | 12 meses (dosis única) | NV Ene–Dic 2023 | SRCeI |
| SRP 1° | 12 meses | NV Ene–Dic 2023 | SRCeI |
| SRP 2° | 36 meses | NV Ene–Dic 2021 | SRCeI |
| Hepatitis A | 18 meses (dosis única) | NV Jul 2022–Jun 2023 | SRCeI |
| Varicela 1° | 18 meses | NV Jul 2022–Jun 2023 | SRCeI |
| Varicela 2° | 36 meses | NV Ene–Dic 2021 | SRCeI |
| Neumocócica Polisacárida | 65 años | Proyección INE 65 años 2024 | INE |
| dTpa 1° básico | Refuerzo escolar | Matrícula 1° básico 2024 | Mineduc |
| dTpa 8° básico | Refuerzo escolar | Matrícula 8° básico 2024 | Mineduc |
| VPH 4° básico | Dosis única nonavalente (+ 1° dosis rezagados) | Matrícula 4° básico 2024 | Mineduc |
| VPH 5° básico | 2° dosis tetravalente (solo 2024) | Matrícula 5° básico 2024 | Mineduc |
| dTpa Gestantes | Dosis única ≥ 28 sem | Estimación Prophet *(pendiente)* | SRCeI histórico |

---

## 8. Notas metodológicas importantes

### Numerador escolar solo usa año t
A diferencia de las vacunas infantiles (que incluyen t+1 y t+2), las vacunas escolares y de gestantes **solo usan vacunados del año t**, ya que la estrategia de vacunación escolar ocurre en el año en curso.

### VPH 2024 — transición de esquema
En 2024 coexisten dos esquemas según el Anexo 1 (pág. 26):
- **DOSIS_UNICA** → nonavalente (nuevo desde 2024), 4° básico
- **1RA_DOSIS** → tetravalente rezagados, 4° básico
- **2DA_DOSIS** → tetravalente completando esquema 2023, 5° básico

A partir de 2025 solo persiste el nonavalente dosis única en 4° básico.

### Neumocócica Polisacárida >100%
Es esperado que la cobertura supere 100% porque el numerador incluye **rescate** (personas ≥66 años sin dosis previa), mientras el denominador es solo la proyección de quienes cumplen 65 ese año.

### Meningocócica Recombinante Refuerzo ~15%
El RNI registra el refuerzo con el nombre `VACUNA BEXSERO` en lugar de un nombre que incluya "REFUERZO". La ventana de nacimiento Jul 2022–Jun 2023 puede no coincidir exactamente con todos los registrados. Requiere revisión con el equipo de datos RNI.

### Código de comuna — join escolar
- **RNI:** `COD_COMUNA_OCURR` y `COD_COMUNA_RESID` (formato 5 dígitos, ej: 13101)
- **Mineduc:** `COD_COM_RBD` (mismo formato)
- **SRCeI:** `COMUNA_N` (mismo formato)
- **INE:** `Comuna` (mismo formato, verificado)

---

## 9. Alertas y pendientes

### Alertas activas en resultados 2024

| Vacuna | Cobertura | Estado |
|--------|-----------|--------|
| Meningocócica Recombinante Refuerzo | ~15% | ⚠️ Revisar clasificación en RNI |
| Neumocócica Polisacárida | ~257% | ℹ️ Esperado (incluye rescate 66+) |
| dTpa Gestantes | 0% / inf | ⏳ Pendiente denominador Prophet |

### Pendientes

- [ ] **Denominador gestantes:** construir modelo Prophet con serie histórica NV 1990–2023. Output esperado: `denominador_gestantes_2024.csv` con columnas `COMUNA_N`, `COMUNA`, `GESTANTES_ESTIMADAS`. El script 3 lo carga automáticamente si existe el archivo.
- [ ] **Meningocócica Recombinante Refuerzo:** validar nombre exacto de la vacuna en RNI para el refuerzo de 18 meses.
- [ ] **Cortes preliminares:** al disponerse datos de 2025, reejecutar script 1 con carpeta 2025 disponible → el script detecta automáticamente los años cargados y ajusta la etiqueta de corte (PRIMER CORTE / SEGUNDO CORTE / CORTE FINAL).

---

*Documento generado en base a la Resolución Exenta N°287, Metodología para el Cálculo de Coberturas de Vacunas Programáticas, DEIS — Departamento de Inmunizaciones, versión 2.0 (17-12-2025)*
