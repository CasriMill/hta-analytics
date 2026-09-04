# HTA Analytics - GUI version under construction (comprehensive import/filter/preview/export)

A robust and comprehensive Python library for **Health Technology Assessment (HTA)**. Designed specifically for evaluating medical devices and clinical systems using Multi-Criteria Decision Analysis (MCDA). 

The library supports dynamic data generation, multi-format file imports (CSV/XLSX), variable filtering, dual-mode data normalization, and cutting-edge weight sensitivity analysis.

---

## 🚀 Key Features

* **Multi-Format Data Import**: Seamlessly ingest data from local CSV or Excel (.xlsx) files using a structured metadata layout.
* **Synthetic Data Simulation**: Generate highly realistic evaluation criteria with adjustable standard deviation (`std`) and skewness (`skewness`).
* **Dual Normalization Techniques**:
  * Classical **Min-Max** Normalization.
  * Advanced **Weitendorf** Normalization (Z-score based mapping to mitigate outlier effects).
* **Variant MCDA Engines**:
  * **SAW** (Simple Additive Weighting / Weighted Sum Model).
  * **TOPSIS** (Technique for Order of Preference by Similarity to Ideal Solution).
  * **VIKOR** (ViseKriterijumska Optimizacija I Kompromisno Resenje for compromise ranking).
* **Weight Stability & Sensitivity Analysis**: Automatically discovers stability thresholds using an interval bisection (binary search) algorithm.
* **Advanced Visualizations**: Features descriptive statistical boxplots/violins and a specialized symmetric logarithmic (**SymLog**) weight sensitivity chart.

---

## 🛠️ Installation

Option 1: For Local Users & Developers (From Source)
If you have downloaded the repository source files or extracted the ZIP archive, open your terminal/console, navigate into the project directory, and install it in editable mode:

```bash
cd hta-analytics
pip install -e .
```

Alternatively, once pushed to GitHub, users can install it directly via URL:

```bash
pip install git+https://github.com
```

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

## 💻 Quick Start Usage

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
> Your Name. (2026). *HTA Analytics: A Python library for Multi-Criteria Decision Analysis and Weight Sensitivity in Health Technology Assessment*. GitHub repository. Available at: https://github.com

---

## 📄 License

This project is licensed under the MIT License - feel free to use, modify, and distribute it.
# hta-analytics
