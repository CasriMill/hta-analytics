---
title: 'HTA Analytics: A Python Library and Graphical User Interface for Multi-Criteria Decision Analysis in Health Technology Assessment'
tags:
  - Python
  - Health Technology Assessment
  - MCDA
  - Sensitivity Analysis
  - Technical Evaluation
authors:
  - name: Jiří MILLEK
    orcid: 0000-0002-5834-7184
    affiliation: 1
affiliations:
  - name: Independent Researcher, Czechia
    index: 1
date: 29 September 2026
bibliography: paper.bib
---

# Summary
Health Technology Assessment (HTA) is a formal, multidisciplinary process used to evaluate the clinical, economic, and technical value of medical devices and healthcare technologies [@rogalewicz2016hta]. Clinical procurement boards are frequently faced with the challenge of selecting medical systems based on highly heterogeneous, conflicting criteria (e.g., purchase cost, warranty length, software interoperability, and clinical throughput). 

`hta-analytics` is a comprehensive Python package accompanied by an intuitive Graphical User Interface (GUI) engineered to run Multi-Criteria Decision Analysis (MCDA) tailored for HTA requirements. The software bridges the gap between advanced decision-science methodologies and clinical administrators, enabling comprehensive analytical pipelines without requiring any programming knowledge.

# Statement of Need
While independent mathematical packages for single MCDA methods are available across various open-source ecosystems, existing solutions lack integrated end-to-end pipelines that reflect the empirical workflows of clinical managers. Hospital decision-makers require an environment that supports data ingestion, structural filtering, and mathematical adjustments within a centralized application. Furthermore, determining the robustness of a ranking against variations in criteria weight profiles typically requires complex, custom simulation scripts.

## State of the field

While several Multi-Criteria Decision Analysis (MCDA) libraries exist in the Python ecosystem—such as `scikit-criteria` or `pyMCDA`—they often target general-purpose operations and require programming literacy. `hta-analytics` fills a critical gap in Health Technology Assessment (HTA) by bundling robust out-of-the-box normalization algorithms tailored to medical equipment constraints (e.g., Weitendorf, Jüttler-Körth) with an accessible graphical interface. Furthermore, it introduces a dedicated interval bisection algorithm for high-precision weight sensitivity analysis, which is rarely integrated seamlessly into existing non-programmer HTA toolsets.

## Software design

The `hta-analytics` architecture follows a modular, decoupled approach separating the core mathematical computational backend from the presentation layer. 
- **Core Engine (`hta` package):** Encapsulates the multi-criteria calculation matrices (SAW, TOPSIS, VIKOR, AHP, CORPAS), missing-data filtering, and mathematical normalization functions. 
- **Sensitivity Core:** Implements a binary-search (interval bisection) workflow to systematically locate weight stability thresholds.
- **Graphical User Interface (GUI):** A standalone desktop presentation view constructed using Python's interface libraries, providing direct metadata-aware file ingestion (CSV/XLSX) and visual rendering components (Matplotlib logs plots) without coupling business logic to user-interface states.

## Research impact statement

In healthcare management, selecting biomedical technology involves multi-faceted tradeoffs across costs, clinical efficacy, and compliance metrics. `hta-analytics` directly impacts clinical engineering and health economics research by democratizing mathematical decision-frameworks. A key strength of the software is its intuitive, metadata-aware filtering pipeline, which allows researchers to easily enforce knockout conditions based on categorical or boolean characteristics (such as CE certification) prior to analysis. 

More importantly, the software fundamentally improves how weight sensitivity is evaluated. Standard sensitivity practices in Health Technology Assessment (HTA) typically analyze only one selected criterion at a time, treating it as an isolated, secondary task. In contrast, `hta-analytics` automates this process by instantly calculating and testing stability thresholds across all utilized characteristics simultaneously. This comprehensive, unified approach to sensitivity profiling dramatically reduces manual analytical overhead, eliminates researcher bias in selecting which criteria to test, and provides a highly robust validation of the overall decision framework through a single, cohesive workflow.


## AI usage disclosure

The author acknowledges the use of AI-assisted development tools (such as GitHub Copilot / Large Language Models) during the design of the graphical user interface layout and test coverage components. All core mathematical formulations, normalization logic, and interval bisection sensitivity engines were strictly audited, verified, and manually implemented by the author to guarantee mathematical accuracy.


`hta-analytics` addresses these operational gaps by delivering a feature-rich, production-ready framework. The architectural contributions of the library are structured into five core pipelines:

* **Data Ingestion and Standardization**: Supports flexible multi-format data imports (including Excel sheets and CSV datasets) containing complex technical metrics and heterogeneous medical parameters.
* **Condition-Based Knockout Filtering**: Employs customizable logical evaluation engines allowing users to filter alternatives based on strict baseline constraints (e.g., mandatory certifications or minimum clinical capacity thresholds).
* **Criteria Weight Control**: Provides interactive controls to adjust, normalize, and distribute importance weights across competing analytical attributes under mathematical consistency constraints.
* **Algorithmic Variety and Custom Normalization**: Features a wide array of linear and compromise decision models including Simple Additive Weighting (SAW) [@maccrimmon1968decision], TOPSIS [@hwang1981topsis], and VIKOR [@opricovic2004vikor]. Scaling discrepancies among disparate indicators are resolved through eight dual-mode benefit/cost normalization transformations evaluated by @vafaei2016normalization.
* **High-Precision Sensitivity Profiling**: Automates structural validation by incorporating an advanced weight sensitivity profiling engine driven by an interval bisection (binary search) algorithm based on the framework introduced by @millek2019sensitivity. The software dynamically calculates stability thresholds and projects weight limits using customized symmetric logarithmic (**SymLog**) visualizations.

By offering both an autonomous GUI application for clinical staff and a documented Python API for reproducible research, `hta-analytics` facilitates sound, auditable, and mathematically transparent decisions in health technology procurement.

# Acknowledgements
The author would like to express gratitude to the open-source community for providing foundational infrastructure libraries, notably NumPy, Pandas, Matplotlib, and PySide6.
