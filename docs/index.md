# Sentinel-1 SAR Backscatter Analysis Ready Data Preparation in Google Earth Engine

[![Release](https://img.shields.io/github/v/release/mateuspinto/ee-s1-ard)](https://img.shields.io/github/v/release/mateuspinto/ee-s1-ard)
[![Build status](https://img.shields.io/github/actions/workflow/status/mateuspinto/ee-s1-ard/main.yml?branch=main)](https://github.com/mateuspinto/ee-s1-ard/actions/workflows/main.yml?query=branch%3Amain)
[![Commit activity](https://img.shields.io/github/commit-activity/m/mateuspinto/ee-s1-ard)](https://img.shields.io/github/commit-activity/m/mateuspinto/ee-s1-ard)
[![License](https://img.shields.io/github/license/mateuspinto/ee-s1-ard)](https://img.shields.io/github/license/mateuspinto/ee-s1-ard)

This implementation enhances the Sentinel-1 SAR Backscatter ARD Preparation framework by making it a PyPI package.

## Features
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `geometry` | `ee.Geometry` | Area of interest | Required |
| `start_date` | `str` | Start date (YYYY-MM-DD) | Required |
| `stop_date` | `str` | End date (YYYY-MM-DD) | Required |
| `polarization` | `str` | Polarization (`VV`, `VH`, `VVVH`) | `VVVH` |
| `apply_border_noise_correction` | `bool` | Apply border noise correction | `True` |
| `apply_terrain_flattening` | `bool` | Apply terrain flattening | `True` |
| `apply_speckle_filtering` | `bool` | Apply speckle filtering | `True` |
| `output_format` | `str` | Output format (`LINEAR`, `DB`) | `DB` |

---

## Installation
Make sure you have the `earthengine-api` installed:

```bash
pip install ee-s1-ard
```

Authenticate with Google Earth Engine:

```bash
earthengine authenticate
```

---

## Usage

### 1. Import the library and create an instance:
```python
import ee

# Initialize the GEE API
ee.Initialize()

from ee-s1-ard import S1ARDImageCollection

# Define input parameters
geometry = ee.Geometry.Polygon(
    [[[5.0, 50.0], [5.5, 50.0], [5.5, 50.5], [5.0, 50.5], [5.0, 50.0]]]
)
start_date = '2021-01-01'
stop_date = '2021-12-31'

processor = S1ARDImageCollection(
    geometry=geometry,
    start_date=start_date,
    stop_date=stop_date,
    polarization="VVVH",
    apply_border_noise_correction=True,
    apply_terrain_flattening=True,
    apply_speckle_filtering=True,
    output_format="DB"
)
```

### 2. Get the processed collection:
```python
collection = processor.get_collection()
```

### 3. Example: Display the collection in GEE:
```python
import geemap

Map = geemap.Map()
Map.centerObject(geometry, 10)
Map.addLayer(collection.mean(), {'min': -25, 'max': 0}, 'Sentinel-1')
Map
```

---

## Notes
- The processed collection is ready for analysis and visualization.
- Speckle filtering and terrain flattening are optional but improve data quality.
- Output in dB scale is suitable for most applications.
```

---

## Why forking?

I DO NOT OWN THE SOLUTION MADE HERE. All credits go to the author and original paper, duly referenced here. My purpose was simply to make the code more pythonic, with checks (mypy), and create a package on Pypi, in order to be easily usable in several academic and production solutions.

## Testing the solution in SITS (Satellite Image Time Series) for agriculture

![sits](https://github.com/user-attachments/assets/6fac0b67-0567-4829-b2fa-88d7f58a264e)

## Testing the solution in a single agriculture image

### Raw image (from GEE)
![raw](https://github.com/user-attachments/assets/a436a71f-9d80-4d27-8f15-692f8dec7683)


### GRD image (preprocessed in GEE)
![grd](https://github.com/user-attachments/assets/e2a7a372-b9d5-443b-a3bc-970e194436a4)


### ARD image (this solution)
![ard](https://github.com/user-attachments/assets/cca067ee-baaa-45b2-b11b-4840e2077560)
