# Data

Source: National Institute of Statistics of Romania (INS), statistical survey on tourist accommodation capacity and activity (TUR1A) and the TEMPO-Online database. The files were obtained from the Gorj County Statistics Directorate. Reference period: 2001–2025; data extracted in September 2026 (2025 may be revised by INS).

## Raw files (`raw/`)

| Folder / file | Content (TEMPO table) | Level |
|---|---|---|
| `tempo_panel/capacitati cazare turism 2001-2025.xlsx` | capacity in operation, bed-days (TUR103D) | locality × type × year |
| `tempo_panel/sosiri turisti 2001-2025.xlsx` | arrivals (TUR104E) | locality × type × year |
| `tempo_panel/innoptari turisti 2001-2025.xlsx` | overnight stays (TUR105E) | locality × type × year |
| `tempo_panel/sosiri turisti romani-straini 2001-2025.xlsx` | arrivals by residence (TUR104B) | county × type × year |
| `tempo_panel/innoptari turisti romani-straini 2001-2025.xlsx` | overnight stays by residence (TUR105D) | county × type × year |
| `tur1a_2024/`, `tur1a_2025/` | detailed TUR1A reports (by category, tourist zone, country of origin) | used only for cross-checks |

A colon (`:`) marks an empty cell. Additivity checks (county, type and locality totals against the sums of their components, 1,225 per indicator) show no discrepancy, so the colon is read as absence of activity and nothing is imputed.

## Processed files (`processed/`, built by `build_processed.py`)

### `panel_long.csv`

`structure_type`, `siruta`, `locality`, `year`, `capacity_bed_days`, `arrivals`, `overnight_stays`. Rows with `locality = TOTAL` are type totals; `structure_type = Total` is the sum over types.

### `county_series.csv`

Annual county series: capacity, arrivals and overnight stays for the total, hotels and agritourism guesthouses; `capacity_other` = total − hotels − agritourism.

### `county_by_residence.csv`

`indicator`, `structure_type`, `residence` (all / Romanian / foreign), `year`, `value`.

### `panel_model_agro.csv`

Forecasting panel: one row per locality and year with positive capacity, arrivals and overnight stays in agritourism guesthouses (292 rows).

| Feature | Meaning |
|---|---|
| `trend` | years since 2001 |
| `crisis_dummy` | 1 in 2008–2010 |
| `pandemic_dummy` | 1 in 2020–2021 |
| `log_capacity_agro` | log of current agritourism capacity of the locality |
| `years_of_experience` | number of earlier years with agritourism data |
| `log_capacity_county`, `log_overnight_county` | log of county totals in the same year |
| `agro_share_county_capacity` | agritourism share of county capacity (%) |
| `hist_mean_log_overnight`, `hist_mean_occupancy`, `hist_mean_stay` | expanding means over earlier years only |
| `has_lag` | 1 if the previous year is available |
| `lag1_log_overnight`, `lag1_log_capacity` | previous year's values |
| `y_ln1p_overnight_stays` | target, ln(1 + overnight stays) |

Missing history values are left empty here; the models fill them with means computed on the training rows only.

## Definitions

* **Capacity in operation** (bed-days): beds multiplied by the days the units are open.
* **Arrivals**: persons staying at least one night in a tourist accommodation unit.
* **Overnight stay**: a 24-hour period for which a person is registered in the unit.
* **Occupancy rate** (net utilisation index) = 100 × overnight stays / capacity.
* **Agritourism**: the INS category “agritourism guesthouses” (*pensiuni agroturistice*).
