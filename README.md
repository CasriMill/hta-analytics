# HTA Analytics GUI 0.4.0

A graphical application and Python library for **Health Technology Assessment (HTA)**. The GUI is designed for evaluating medical devices and clinical systems using Multi-Criteria Decision Analysis (MCDA), without requiring users to write Python code.

The library supports dynamic data generation, multi-format file imports (CSV/XLSX), variable filtering, dual-mode data normalization, and cutting-edge weight sensitivity analysis.

---

## 🚀 Key Features

* **Multi-Format Data Import**: Seamlessly ingest data from local CSV or Excel (.xlsx) files using a structured metadata layout.
* **Synthetic Data Simulation**: Generate highly realistic evaluation criteria with adjustable standard deviation (`std`) and skewness (`skewness`).
* **MCDA Normalization Techniques**:
  * **Min-Max** and **Weitendorf** range normalization.
  * **MAX/Jüttler**, **Jüttler-Körth**, **SUM**, **VECTOR**, **SIGMOID**, and **Peldchus**.
* **Variant MCDA Engines**:
  * **SAW** (Simple Additive Weighting / Weighted Sum Model).
  * **TOPSIS** (Technique for Order of Preference by Similarity to Ideal Solution).
  * **VIKOR** (ViseKriterijumska Optimizacija I Kompromisno Resenje for compromise ranking).
* **Weight Stability & Sensitivity Analysis**: Automatically discovers stability thresholds using an interval bisection (binary search) algorithm.
* **Advanced Visualizations**: Features descriptive statistical boxplots/violins and a specialized symmetric logarithmic (**SymLog**) weight sensitivity chart.

---

### Normalization methods

All methods return values where a higher value means a better alternative. Cost
criteria are therefore inverted where needed. `weitendorf` uses
`(r - r_min) / (r_max - r_min)` for benefits and
`(r_max - r) / (r_max - r_min)` for costs. `max` (alias `juttler`) uses
`r / r_max` for benefits and `1 - r / r_max` for costs. `juttler_korth`
uses `r_min / r` for costs. `sum` uses inverse values for costs and direct
values for benefits; `vector` divides by the Euclidean norm. `sigmoid` uses
the specified function `1 / (1 + exp((r - median) / IQR))` for costs and its
complement for benefits. `peldchus_t=1` is Weitendorf; the GUI offers the
explicit variants `Peldchus t=2` and `Peldchus t=3`. Larger values emphasize
departures above and below the mean.
Constant criteria normalize to `1` and are removed from MCDA when they cannot
distinguish active alternatives.

## 🛠️ Installation

Option 1: For Local Users & Developers (From Source)
If you have downloaded the repository source files or extracted the ZIP archive, open your terminal/console, navigate into the project directory, and install it in editable mode:

```bash
cd hta-analytics
pip install -e .
```

For this GUI release, install the tagged version directly from GitHub:

```bash
pip install "git+https://github.com/CasriMill/hta-analytics.git@v0.4.0"
```

---

## 🚀 Start the GUI

After installation, start the application from a terminal with:

```bash
python -m hta.gui_main
```

The GUI opens with the **Import** tab. From there you can load a CSV/XLSX
evaluation sheet or generate demo data, review the import protocol, edit
weights, apply filters, run MCDA, and export results and charts.

The repository can also be downloaded as a ZIP archive. After extracting it,
open a terminal in the project directory, install the dependencies with
`pip install -e .`, and run the same command above.

---

## Workflow in the GUI

1. Use **Load data file** to import a CSV/XLSX file with the metadata rows
   described below, or use **Generate demo data**.
2. Open **Weights** and check the imported weights. Set a weight to zero when
   a criterion should be used only for filtering; negative weights are invalid.
3. Use **Filters** to apply knockout conditions and confirm the filtered
   device count.
4. Select an MCDA method and normalization, then press **Run MCDA**. If
   manually edited weights exclude criteria, confirm the exclusion dialog.
5. Review **Results**, then use the export buttons for CSV/XLSX output.
6. Open **Graphs** to inspect ranking and weight-sensitivity charts and export
   the PNG charts at high resolution.

The **Help / Workflow** button in the GUI opens this README directly.

The repository also contains `mcda_demo_errors.csv`, a deliberately invalid
sample for testing import validation. It demonstrates invalid boolean, integer,
float, missing numeric values, categorical values containing numbers, and a
negative imported weight.

---

## 📊 File Layout (Approach A - Metadata Aware)

To enable automatic detection of data types (`int`/`float`/`bool`), criteria directions (`benefit`/`cost`), and localization, structure your CSV/XLSX files with the following mandatory top rows:

| Device_ID | price | efficiency | ce_cert |
| :--- | :--- | :--- | :--- |
| **HTA_Type** | cost | benefit | benefit |
| **HTA_Dtype** | int | float | bool |
| **HTA_FullName** | Purchase Price (EUR) | Clinical Efficiency (%) | CE Certification |
| **Device_1** | 120000 | 92.4 | True |
| **Device_2** | 95000 | 81.0 | False |

---

## 💻 Python library API

The GUI is the recommended entry point for this release. The underlying
`HTA` class remains available for scripted analyses and reproducible
workflows:

```python
from hta import HTA

# 1. Initialize the analyzer
hta = HTA()

# 2. Load your custom evaluation sheet (automatically parses 13+ criteria)
hta.load_data("mcda_demo_data.csv")

# 3. Define raw un-normalized weights (e.g., scoring points 1-10)
importance_weights = {
    "price": 8,
    "efficiency": 10,
    "supplies": 5,
    "ce_cert": 0
}
hta.set_weights(importance_weights)

# 4. Enforce strict exclusion/knock-out criteria
hta.apply_filters({"ce_cert": True})

# 5. Run your preferred MCDA configuration (e.g., Weitendorf + SAW)
results = hta.run_mcda(method="SAW", norm_method="weitendorf")
print(results)

# 6. Render the symmetric log-scale weight stability tolerance plot
hta.plot_relative_stability_delta(method="SAW", norm_method="weitendorf")
```

---

## 🧪 Testing

The library includes automated checks to maintain mathematical consistency. To run the validation tests, make sure `pytest` is installed and run:

```bash
pytest
```

---

## 🎓 Citation & Authorship

If you use this software or its computational methods in your academic research, please attribute the author by citing this repository and referencing the ORCID identifier:

* **Author:** MILLEK Jiri
* **ORCID:** [https://orcid.org/0000-0002-5834-7184]

**Suggested Citation Format:**
> Your Name. (2026). *HTA Analytics: A Python library for Multi-Criteria Decision Analysis and Weight Sensitivity in Health Technology Assessment*. GitHub repository. Available at: https://github.com/CasriMill/hta-analytics

---

## 📄 License

This project is licensed under the MIT License - feel free to use, modify, and distribute it.
# hta-analytics
