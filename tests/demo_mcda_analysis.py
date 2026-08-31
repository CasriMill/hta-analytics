#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTA Analytics - Demo MCDA Analysis
===================================
Demonstration script showing complete workflow:
1. Loading external data (CSV)
2. Running MCDA analysis (SAW, TOPSIS, VIKOR)
3. Weight sensitivity analysis
4. Results visualization
"""

import sys
import os

# Add parent directory to path so we can import hta module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hta.analyzer import HTA

print("\n" + "="*90)
print("   HTA ANALYTICS - DEMONSTRATION OF MCDA WORKFLOW")
print("="*90 + "\n")

# Inicializace
hta = HTA()

# Načtení dat - správná cesta
data_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mcda_demo_data_weight_8devices.csv")
success = hta.load_data(data_file)

# MCDA analýza
print("\n📊 STEP 1: Data Overview and Descriptive Statistics")
print("-" * 90)
hta.plot_descriptive_stats(cols_per_row=3)

print("\n🔍 STEP 2: Running MCDA Analysis WITHOUT filters (all devices accepted)")
print("-" * 90)
results = hta.run_mcda(method="SAW", norm_method="minmax")
hta.print_results()

print("\n🔍 STEP 2B: Running MCDA Analysis WITH filter (ce_cert=True required)")
print("-" * 90)
print("   Applying filter: devices must have ce_cert=True")
hta.apply_filters({'ce_cert': True})
results_filtered = hta.run_mcda(method="SAW", norm_method="minmax")
hta.print_results()
print("   Note: Device_4 is excluded due to ce_cert=False\n")

# Sensitivity analýza
print("\n⚙️  STEP 3: Performing Weight Sensitivity Analysis")
print("-" * 90)
print("    (This may take a moment...)\n")
hta.find_stability_intervals()
hta.print_results()

# Grafy
print("\n📈 STEP 4: Visualizing Weight Stability Bounds")
print("-" * 90)
hta.plot_relative_stability_delta()

print("\n" + "="*90)
print("   ✅ DEMO COMPLETED SUCCESSFULLY!")
print("="*90)
print(f"\n💾 Results are stored in: hta.results")
print(f"   Call hta.print_results() anytime to display them\n")