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
  - name: Czech Technical University in Prague, Czech Republic, Faculty of Biomedical Engineering, Department of Information and Communication Technologies in Medicine
    index: 1
date: 29 September 2026
bibliography: paper.bib
---

# Summary
Health Technology Assessment (HTA) is a multidisciplinary process that summarizes information about the medical, social, economic, and ethical issues related to the use of a health technology. A critical component of HTA is the technical and clinical evaluation of medical devices, which inherently involves multiple conflicting criteria (e.g., purchase price, clinical efficiency, and certification status). 

`hta-analytics` is a comprehensive Python library and graphical user interface (GUI) designed to streamline Multi-Criteria Decision Analysis (MCDA) for HTA processes. The software bridges the gap between complex mathematical decision-making algorithms and non-technical healthcare managers, allowing users to execute data ingestion, variable filtering, criteria normalization, and robust weight sensitivity profiling without writing any code.

# Statement of Need
While several specialized MCDA packages exist in the R and Python ecosystems, they typically require programming proficiency and often focus on a single family of algorithms. In clinical environments and hospital management, decision-makers who evaluate medical devices (such as X-ray machines, ventilators, or clinical systems) often lack data science skills. Furthermore, traditional tools rarely provide automated, high-precision tools for analyzing how sensitive the final ranking is to changes in criteria weights.

`hta-analytics` addresses these challenges by offering a fully integrated, production-ready workflow within a single application. The primary contributions of the library include:

* **Comprehensive Pipeline Integration**: Seamlessly handles the entire evaluation lifecycle—from multi-format metadata-aware data imports (CSV/XLSX) and condition-based knockout filtering to final ranking export.
* **Algorithmic Variety**: Implements multiple standard MCDA engines, including Simple Additive Weighting (SAW), Technique for Order of Preference by Similarity to Ideal Solution (TOPSIS), and VišeKriterijumska Optimizacija I Kompromisno Rešenje (VIKOR).
* **Outlier-Robust Normalization**: Supports eight distinct dual-mode normalization methods (e.g., Min-Max, Weitendorf, Jüttler-Körth, Sigmoid, and Peldchus) tailored to correctly process both benefit and cost criteria.
* **Advanced Sensitivity Analysis**: Features a cutting-edge weight stability profiling engine powered by an interval bisection (binary search) algorithm. It automatically discovers precise stability thresholds and visualizes them using custom symmetric logarithmic (**SymLog**) charts.

By combining an intuitive Graphical User Interface with a scripted Python API for reproducible research, `hta-analytics` empowers hospital procurement committees and HTA professionals to make rigorous, transparent, and mathematically sound decisions.

# Acknowledgements
The author would like to thank the open-source community for the foundational tools used in this project, including NumPy, Pandas, and Matplotlib.
