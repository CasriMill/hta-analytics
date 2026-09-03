# -*- coding: utf-8 -*-
"""
HTA Analytics — Core Computational Engine
========================================
A comprehensive module for Health Technology Assessment (HTA).
Provides load data from "CSV/XLSX" or synthetic data generation,
variant multi-criteria decision analysis (MCDA) by methods: TOPSIS, SAW and VIKOR,
with variant normalization techniques (Min-Max, Weitendorf),
and robust weight sensitivity assessment using interval bisection algorithms.

:authors:     MILLEK Jiri  <jiri.millek@fbmi.cvut.cz> [https://orcid.org/0000-0002-5834-7184]
:copyright:   (c) 2026 MILLEK Jiri / CASRI, p.o. MoD Czech Republic && Czech Technical University in Prague, Faculty of Biomedical Engineering dept. Information and Communication Technologies in Medicine
:license:     MIT License
:version:     0.1.6
:status:      Open Source
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats as stats
            
class HTA:
    """
    Health Technology Assessment (HTA) Evaluator.
    Handles data import, variant multi-criteria decision making, 
    and advanced sensitivity profiling for medical devices.
    """
    def __init__(self, n_devices=None, variables_config=None):
        """
        Initialize the HTA framework.
        
        :param n_devices: Int, number of mock devices to generate. If None, awaits file import via load_data().
        :param variables_config: Dict, optional custom configuration for variables/criteria.
        """
        self.n_devices = n_devices
        
        # Configuration dictionary starts empty unless the user supplies their own definition.
        # It is populated dynamically from metadata rows in the imported file.
        self.variables_config = {} if variables_config is None else variables_config
            
        self.raw_data = None
        self.weights = None
        self.normalized_data = None
        self._silence_info = False
        
        # Results storage structure (populated after run_mcda)
        self.results = None
        
        # If the user still specifies the number of devices (synthetic generation path),
        # use the default English/Czech-compatible configuration set.
        if self.n_devices is not None:
            self.variables_config = {
                "price": {"full_name": "Purchase Price (EUR)", "range": (100000, 200000), "type": "cost", "dtype": "int", "std": 30000, "skewness": -5, "round_to": -2},
                "op_costs": {"full_name": "Annual Operational Costs (EUR)", "range": (1000, 5000), "type": "cost", "dtype": "int", "round_to": -2},
                "efficacy": {"full_name": "Clinical Efficacy of Procedure (%)", "range": (70, 99), "type": "benefit", "dtype": "float", "std": 6, "skewness": -2, "round_to": 1},
                "consumables": {"full_name": "Consumables Cost per Examination (EUR)", "range": (5, 20), "type": "cost", "dtype": "float", "std": 2, "skewness": 1.5, "round_to": 1},
                "training": {"full_name": "Staff Training Cost per Course (EUR)", "range": (500, 2000), "type": "cost", "dtype": "float", "std": 300, "skewness": 1.2, "round_to": 0},
                "accuracy": {"full_name": "Measurement Accuracy Level (‰)", "range": (975, 999), "type": "benefit", "dtype": "int", "std": 3, "skewness": 1.5},
                "service_life": {"full_name": "Post-Warranty Support & Parts Availability (years)", "range": (3, 10), "type": "benefit", "dtype": "int"},
                "ce_cert": {"full_name": "CE Certification Status", "type": "benefit", "dtype": "bool", "prob_true": 0.99},
                "connectivity_eth": {"full_name": "Ethernet Network Connectivity", "type": "benefit", "dtype": "bool", "prob_true": 0.8},
                "connectivity_wifi": {"full_name": "Wireless WiFi Connectivity", "type": "benefit", "dtype": "bool", "prob_true": 0.8},
                "connectivity_usb": {"full_name": "USB Data Interface Support", "type": "benefit", "dtype": "bool", "prob_true": 0.9},
                "connectivity_his": {"full_name": "Hospital Information System (HIS) Integration", "type": "benefit", "dtype": "bool", "prob_true": 0.95},
                "protocol_hl7": {"full_name": "HL7 Protocol Compliant Data Structure", "type": "benefit", "dtype": "bool", "prob_true": 0.65},
            }

            self.devices = [f"Device_{i+1}" for i in range(self.n_devices)]
            self.filtered_devices = list(self.devices)
            self.generate_data()
        else:
            self.devices = []
            self.filtered_devices = []

    def load_data(self, file_path):
        """
        Loads external data (CSV/XLSX) and gets its configuration.
        
        CSV data format sample:
        Device_ID;price;effitiency;weight;ce_cert
            HTA_Type;cost;benefit;cost;benefit
            HTA_Dtype;int;float;int;bool
            HTA_FullName;desc of price; desc of effitiency; desc of product weight; identification of CE certification
            HTA_Weight;0.25;0.35;0.15;0.25
            Device_1;3500000;85.5;2;True
            Device_2;2800000;72.0;5;False
        
        Metadata rows (all optional except HTA_Type and HTA_Dtype):
        - HTA_Type:      Specifies criterion type ('cost' or 'benefit')
        - HTA_Dtype:     Data type ('int', 'float', or 'bool')
        - HTA_FullName:  Long descriptive name for the variable (optional)
        - HTA_Weight:    Weight values for MCDA (optional; if not present, must be set via set_weights())
        
        If HTA_Weight row is found, weights are automatically imported and processed.
        If not found, a warning is displayed and you must call set_weights() manually.
        """
        print(f"\n📂 Reading international HTA data from file: {file_path}")
        try:
            # Load the source file (automatic separator detection for CSV)
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, index_col=0, sep=None, engine='python')
            elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                df = pd.read_excel(file_path, index_col=0)
            else:
                raise ValueError("Unsupported file format. Use .csv or .xlsx with sep=';' and decimal = '.'!")
            
            # --- EXTRACT METADATA FROM THE FILE HEADER ---
            types_row = df.loc["HTA_Type"]
            dtypes_row = df.loc["HTA_Dtype"]
            
            # Handle the optional full-name row; if missing, fall back to the short name.
            if "HTA_FullName" in df.index:
                full_names_row = df.loc["HTA_FullName"]
                rows_to_drop = ["HTA_Type", "HTA_Dtype", "HTA_FullName"]
            else:
                full_names_row = None
                rows_to_drop = ["HTA_Type", "HTA_Dtype"]
            
            # Handle optional weights row
            weights_imported = False
            if "HTA_Weight" in df.index:
                weights_row = df.loc["HTA_Weight"]
                rows_to_drop.append("HTA_Weight")
                weights_imported = True
            else:
                weights_row = None
            
            # Dynamically build the internal variables_config dictionary
            self.variables_config = {}
            for col in df.columns:
                self.variables_config[col] = {
                    "type": str(types_row[col]).strip().lower(),
                    "dtype": str(dtypes_row[col]).strip().lower(),
                    "full_name": str(full_names_row[col]).strip() if full_names_row is not None else str(col)
                }
            
            # --- CLEAN DATA WITHOUT METADATA ---
            # drop comment and configuration rows
            self.raw_data = df.drop(rows_to_drop)
            
            # Re-type columns according to the imported metadata
            for col in self.raw_data.columns:
                dt = self.variables_config[col]["dtype"]
                if dt == "int":
                    self.raw_data[col] = pd.to_numeric(self.raw_data[col]).round().astype(int)
                elif dt == "float":
                    self.raw_data[col] = pd.to_numeric(self.raw_data[col]).astype(float)
                elif dt == "bool":
                    # Convert values such as 'True'/'False' or 1/0 into proper boolean types
                    self.raw_data[col] = self.raw_data[col].map({'True': True, 'False': False, 1: True, 0: False, True: True, False: False})
            
            # Set internal attributes based on the imported dataset
            self.devices = list(self.raw_data.index)
            self.filtered_devices = list(self.devices)
            self.n_devices = len(self.devices)
            
            print(f"✅ Succesfull import of {self.n_devices} devices.")
            
            # --- PROCESS IMPORTED WEIGHTS (IF PRESENT) ---
            if weights_imported:
                try:
                    # Convert weights_row to numeric dictionary
                    weights_dict = {}
                    for col in weights_row.index:
                        try:
                            weights_dict[col] = float(weights_row[col])
                        except (ValueError, TypeError):
                            pass  # Skip invalid weight values
                    
                    if weights_dict:
                        self.set_weights(weights_dict)
                        print(f"📊 Weights imported successfully from file:")
                        for var, weight in self.weights.items():
                            full_name = self.variables_config.get(var, {}).get("full_name", var)
                            print(f"   • {var:20s} ({full_name:45s}): {weight:.4f}")
                    else:
                        print(f"⚠️  Weights row found but all values are invalid. Using default equal weights.")
                        self.set_weights({col: 1.0 for col in self.variables_config.keys()})
                except Exception as e:
                    print(f"⚠️  Error processing weights: {str(e)}")
                    print(f"   Using default equal weights instead.")
                    self.set_weights({col: 1.0 for col in self.variables_config.keys()})
            else:
                print(f"⚠️  No weight row (HTA_Weight) found in the file.")
                print(f"   ⓘ  Weights are required for MCDA analysis.")
                print(f"   → Please provide weights using: set_weights({{...}}) or add HTA_Weight row to your CSV/XLSX file.")
            
            # Run the data consistency check to confirm there are no NaN or invalid values.
            return self.validate_data()
            
        except Exception as e:
            print(f"❌ Critical error in import of file: {str(e)}")
            self.raw_data = None
            return False

    def validate_data(self):
        """Perform strict validation of the format and consistency of loaded or generated data."""
        if self.raw_data is None:
            print("❌ Critical error: No data has been loaded for validation.")
            return False
            
        is_consistent = True
        print("\n🔍 DATA FORMAT AND CONSISTENCY TEST HAS STARTED...")
        
        if self.raw_data.isna().sum().sum() > 0:
            print("   ⚠️ Warning: The table contains empty or undefined values (NaN)!")
            is_consistent = False
            
        for short_name in self.variables_config.keys():
            if short_name not in self.raw_data.columns:
                print(f"   ❌ Critical error: Required column '{short_name}' is missing from the dataset!")
                is_consistent = False
                continue
                
            cfg = self.variables_config[short_name]
            series = self.raw_data[short_name]
            dtype = cfg.get("dtype", "float")
            
            if dtype == "bool":
                if not series.isin([True, False, 0, 1, 0.0, 1.0]).all():
                    print(f"   ❌ Type error: Column '{short_name}' should be BOOL but contains other values!")
                    is_consistent = False
            elif dtype == "int":
                if not np.equal(series, series.astype(int)).all():
                    print(f"   ⚠️ Warning: Column '{short_name}' should be INT but contains decimal values!")
                    
            if dtype != "bool" and "range" in cfg:
                low, high = cfg["range"]
                if series.min() < low or series.max() > high:
                    print(f"   ⚠️ Range warning: Values in column '{short_name}' exceed the configured range (Current Min: {series.min()}, Max: {series.max()} vs allowed {cfg['range']}).")

        if is_consistent:
            print("🚀 All format and consistency checks passed successfully. Data are valid.")
        else:
            print("⚠️ Inconsistencies were found in the data. Check the output above.")
            
        return is_consistent


    def generate_data(self):
        """Generate synthetic raw data while preserving the intended cost-benefit relationships."""
        data = {}
        for short_name, cfg in self.variables_config.items():
            dtype = cfg.get("dtype", "float")
            
            if dtype == "bool":
                p = cfg.get("prob_true", 0.5)
                data[short_name] = np.random.choice([True, False], size=self.n_devices, p=[p, 1-p])
                continue
                
            low, high = cfg["range"]
            if "std" in cfg or "skewness" in cfg:
                skew = cfg.get("skewness", 0)
                std = cfg.get("std", (high - low) / 4)
                mean = (low + high) / 2
                vals = []
                while len(vals) < self.n_devices:
                    sample = stats.skewnorm.rvs(skew, loc=mean, scale=std, size=self.n_devices * 2)
                    valid_sample = sample[(sample >= low) & (sample <= high)]
                    vals.extend(valid_sample)
                gen_arr = np.array(vals[:self.n_devices])
            else:
                gen_arr = np.random.uniform(low, high, self.n_devices)
                
            round_to = cfg.get("round_to", 0 if dtype == "int" else 2)
            gen_arr = np.round(gen_arr, round_to)
            
            if dtype == "int":
                data[short_name] = gen_arr.astype(int)
            else:
                data[short_name] = gen_arr
                
        # Create the base DataFrame
        self.raw_data = pd.DataFrame(data, index=self.devices)
        
        # =====================================================================
        # INTRODUCE DEPENDENCY (Correlation with price)
        # =====================================================================
        # 1. Sort the whole DataFrame by price ascending (from cheapest to most expensive)
        self.raw_data = self.raw_data.sort_values(by="price", ascending=True)
        
        # 2. If the training variable exists, sort its values and write them back.
        # This ensures: the cheapest device = cheapest training, the most expensive device = most expensive training.
        if "training" in self.raw_data.columns:
            self.raw_data["training"] = np.sort(self.raw_data["training"].values)
            
        # 3. Same approach for accuracy, if defined in the system.
        if "accuracy" in self.raw_data.columns:
            self.raw_data["accuracy"] = np.sort(self.raw_data["accuracy"].values)
            
        # Optional: restore original row ordering at the end (Device_1, Device_2...),
        # so the table remains visually organized while the internal values stay correctly paired.
        self.raw_data = self.raw_data.sort_index()
        
        return self.raw_data


    def plot_descriptive_stats(self, cols_per_row=3):
        """
        Print descriptive statistics and plot a combined violin + scatter chart
        arranged neatly across multiple rows.
        :param cols_per_row: Maximum number of plots (columns) per row.
        """
        numeric_cols = [c for c, cfg in self.variables_config.items() if cfg.get("dtype") != "bool"]
        n_plots = len(numeric_cols)
        
        print("\n--- Descriptive statistics imported data ---")
        stats_df = self.raw_data[numeric_cols].describe().T
        stats_df["full_name"] = [self.variables_config[c]["full_name"] for c in numeric_cols]
        print(stats_df[["full_name", "count", "mean", "std", "min", "max"]])
        
        # Calculate required number of rows in the grid
        n_rows = (n_plots + cols_per_row - 1) // cols_per_row
        
        # Dynamically determine figure size based on the number of rows and columns
        fig, axes = plt.subplots(n_rows, cols_per_row, figsize=(4 * cols_per_row, 4.5 * n_rows))
        
        # Convert axes to a one-dimensional array for easier indexing (including 1x1 or 1xN cases)
        if n_plots == 1:
            axes = np.array([axes])
        else:
            axes = axes.flatten()
            
        for i, col in enumerate(numeric_cols):
            ax = axes[i]
            data_to_plot = self.raw_data[col].values
            
            # 1. Draw the violin plot
            parts = ax.violinplot(data_to_plot, showmeans=False, showmedians=True, showextrema=True)
            
            # Adjust violin styling
            for pc in parts['bodies']:
                pc.set_facecolor('#1f77b4')
                pc.set_edgecolor('grey')
                pc.set_alpha(0.6)
            parts['cmedians'].set_color('black')
            parts['cmaxes'].set_color('grey')
            parts['cmins'].set_color('grey')
            
            # 2. Draw the scatter plot with jitter (red points)
            jitter = np.random.normal(1, 0.04, size=len(data_to_plot))
            ax.scatter(jitter, data_to_plot, color='red', alpha=0.7, edgecolors='black', zorder=3)
            
            # Labels and formatting for the subplot
            ax.set_title(self.variables_config[col]["full_name"], fontsize=9, pad=10)
            ax.set_xticks([1])
            ax.set_xticklabels(["Distribution"])
            ax.grid(True, linestyle='--', alpha=0.5)
            
        # 3. Hide unused empty subplots in the grid
        for j in range(i + 1, len(axes)):
            fig.delaxes(axes[j])
            
        plt.tight_layout()
        plt.show()



    def set_weights(self, weights_dict):
        """Normalize any weights so that their total sum equals 1.0."""
        full_weights = {v: weights_dict.get(v, 0.0) for v in self.variables_config.keys()}
        total = sum(full_weights.values())
        if total <= 0: raise ValueError("The sum of weights must be > 0!")
        self.weights = pd.Series({k: v / total for k, v in full_weights.items()})
        return self.weights

    def _normalize_filter_rules(self, filter_spec):
        """Normalize several filter syntaxes into a list of rules."""
        if filter_spec is None:
            return []

        if isinstance(filter_spec, dict):
            if all(isinstance(v, (dict, list, tuple)) for v in filter_spec.values()) and not filter_spec:
                return []

            if all(key not in ("column", "operator") for key in filter_spec.keys()):
                normalized = []
                for col, target_val in filter_spec.items():
                    normalized.append({"column": col, "operator": "eq", "value": target_val})
                return normalized

            return [filter_spec]

        if isinstance(filter_spec, (list, tuple)):
            normalized = []
            for rule in filter_spec:
                if isinstance(rule, dict):
                    normalized.append(rule)
                else:
                    raise ValueError(f"Unsupported filter rule format: {rule!r}")
            return normalized

        raise ValueError(f"Unsupported filter specification: {filter_spec!r}")

    def _evaluate_filter_rule(self, rule):
        """Evaluate a single rule and return a boolean Series mask."""
        if not isinstance(rule, dict):
            raise ValueError(f"Filter rule must be a dict, got {type(rule).__name__}")

        col = rule.get("column") or rule.get("col")
        operator = str(rule.get("operator") or rule.get("op") or "eq").lower()

        if col is None:
            raise ValueError("A filter rule must contain a 'column' key.")
        if col not in self.raw_data.columns:
            raise KeyError(f"Column '{col}' does not exist in the current dataset.")

        series = self.raw_data[col]
        if operator == "eq":
            value = rule.get("value")
            return series == value
        if operator == "neq":
            value = rule.get("value")
            return series != value
        if operator == "gt":
            value = rule.get("value")
            return series > value
        if operator == "gte":
            value = rule.get("value")
            return series >= value
        if operator == "lt":
            value = rule.get("value")
            return series < value
        if operator == "lte":
            value = rule.get("value")
            return series <= value
        if operator == "between":
            lower = rule.get("lower")
            upper = rule.get("upper")
            if lower is None or upper is None:
                raise ValueError(f"Filter rule for '{col}' uses 'between' operator but no 'lower'/'upper' values were provided.")
            return (series >= lower) & (series <= upper)

        raise ValueError(f"Unsupported filter operator: '{operator}'")

    def apply_filters(self, filter_spec):
        """Apply one or more exclusion criteria.

        Supported formats:
        - {'ce_cert': True}
        - [{'column': 'ce_cert', 'operator': 'eq', 'value': True}]
        - [{'column': 'price', 'operator': 'between', 'lower': 100000, 'upper': 200000}]
        """
        rules = self._normalize_filter_rules(filter_spec)

        if not rules:
            self.filtered_devices = list(self.devices)
            print("\nNo filter rules applied. All devices remain active.")
            return self.filtered_devices

        mask = pd.Series(True, index=self.raw_data.index)
        for rule in rules:
            mask &= self._evaluate_filter_rule(rule)

        self.filtered_devices = list(self.raw_data.index[mask].tolist())
        print(f"\nFilter rules applied: {rules}. Proceeding with {len(self.filtered_devices)} out of {self.n_devices} devices.")
        return self.filtered_devices

    def export_results(self, output_path):
        """Export the current ranking results to CSV or XLSX."""
        if self.results is None or self.results.get("ranking") is None:
            raise ValueError("No results available. Run run_mcda() before exporting.")

        output_path = str(output_path)
        ranking_df = self.results["ranking"].copy()

        if output_path.lower().endswith(".csv"):
            ranking_df.to_csv(output_path)
        elif output_path.lower().endswith((".xlsx", ".xls")):
            ranking_df.to_excel(output_path)
        else:
            output_path = output_path + ".csv"
            ranking_df.to_csv(output_path)

        print(f"\n💾 Results exported to: {output_path}")
        return output_path

    def normalize_data(self, method="weitendorf"):
        """Alternative normalization methods: 'minmax', 'weitendorf', 'z_score'."""
        self.normalized_data = pd.DataFrame(index=self.devices, columns=self.raw_data.columns)
        
        for col, cfg in self.variables_config.items():
            if cfg.get("dtype") == "bool":
                self.normalized_data[col] = self.raw_data[col].astype(float) if cfg["type"] == "benefit" else 1.0 - self.raw_data[col].astype(float)
                continue
                
            series = self.raw_data[col].astype(float)
            x_min, x_max, x_mean = series.min(), series.max(), series.mean()
            x_std = series.std() if series.std() != 0 else 1.0
            
            if method == "weitendorf":
                if x_max == x_min:
                    self.normalized_data[col] = 1.0
                elif cfg["type"] == "benefit":
                    self.normalized_data[col] = (series - x_min) / (x_max - x_min)
                else:
                    self.normalized_data[col] = (x_max - series) / (x_max - x_min)

            elif method == "minmax":
                if x_max == x_min:
                    self.normalized_data[col] = 0.5
                elif cfg["type"] == "benefit":
                    self.normalized_data[col] = series / x_max
                else:
                    self.normalized_data[col] = 1 - (series / x_max)
                    
            elif method == "z_score":
                z_score = (series - x_mean) / x_std
                z_min, z_max = z_score.min(), z_score.max()
                if z_max == z_min:
                    self.normalized_data[col] = 0.5
                elif cfg["type"] == "benefit":
                    self.normalized_data[col] = (z_score - z_min) / (z_max - z_min)
                else:
                    self.normalized_data[col] = (z_max - z_score) / (z_max - z_min)
        return self.normalized_data

    def _prepare_active_dimensions(self):
        """
        Identify criteria with sufficient statistical variance.
        Filters out criteria where all approved devices share the exact same value.
        
        :return: List of strings representing active columns.
        """
        active_cols = []
        for col in self.variables_config.keys():
            # Use only raw data for devices that passed the filter
            raw_series = self.raw_data.loc[self.filtered_devices, col]
            
            # If there is more than one unique value in the column, it is useful for MCDA
            if raw_series.nunique() > 1:
                active_cols.append(col)
            else:
                # Inform the user that the column is effectively only a filter criterion
                # (printed only when the weight is non-zero)
                if self.weights is not None and self.weights.get(col, 0) > 0:
                    # This message is displayed only during real evaluation, not during sensitivity analysis when weights change repeatedly
                    if hasattr(self, '_silence_info') and not self._silence_info:
                        print(f"ℹ️ Criterion '{col}' is only used as a filter in this context (all approved devices have the same value).")
        return active_cols

    def _adjust_active_weights(self, active_cols):
        """
        STEP 2: Test and recalculate weights.
        Takes the original weights, removes inactive columns, and normalizes the remaining weights to 1.0.
        """
        if self.weights is None:
            self.set_weights({c: 1 for c in self.variables_config.keys()})
            
        # Use weights only for the active criteria
        active_weights = self.weights[active_cols].copy()
        
        # Recalculate the distribution so the sum of active weights is exactly 1.0 (100%)
        if active_weights.sum() > 0:
            active_weights = active_weights / active_weights.sum()
        else:
            # Edge case: if no weight remains, distribute importance evenly
            active_weights = pd.Series(1.0 / len(active_cols), index=active_cols)
            
        return active_weights

    def run_mcda(self, method="SAW", norm_method="minmax"):
        """
        STEP 3: Main MCDA execution method that realizes a clean analytical pipeline:
        dimension cleanup -> weight recalculation -> normalization -> algorithm calculation.
        """
        # Initialize default weights if they have not been set yet
        if self.weights is None:
            self.set_weights({c: 1 for c in self.variables_config.keys()})
            
        # 1. COLUMN ANALYSIS: Find variables that have real discriminating ability
        active_cols = self._prepare_active_dimensions()
        
        # 2. WEIGHT RECALCULATION: Remove irrelevant criteria and normalize the total back to 100%
        active_weights = self._adjust_active_weights(active_cols)
        
        # 3. NORMALIZATION: Run the selected normalization across raw data
        self.normalize_data(method=norm_method)
        
        # Use only approved devices and active columns from the normalized matrix
        active_matrix = self.normalized_data.loc[self.filtered_devices, active_cols].copy()
        
        # Prepare an empty result series for storing scores
        scores = pd.Series(0.0, index=self.devices)
        
        # 4. MCDA METHOD CALCULATION (now works with a guaranteed clean matrix and weights)
        if method == "SAW":
            scores.loc[self.filtered_devices] = active_matrix.multiply(active_weights).sum(axis=1)
            
        elif method == "TOPSIS":
            v_matrix = active_matrix.multiply(active_weights)
            ideal_positive = pd.Series(active_weights, index=active_cols)
            ideal_negative = pd.Series(0.0, index=active_cols)
            
            d_plus = np.sqrt(((v_matrix - ideal_positive)**2).sum(axis=1))
            d_minus = np.sqrt(((v_matrix - ideal_negative)**2).sum(axis=1))
            scores.loc[self.filtered_devices] = d_minus / (d_plus + d_minus)
            
        elif method == "VIKOR":
            v_matrix = active_matrix.multiply(active_weights)
            s = ((active_weights - v_matrix) / active_weights).multiply(active_weights).sum(axis=1)
            r = ((active_weights - v_matrix) / active_weights).multiply(active_weights).max(axis=1)
            
            s_min, s_max = s.min(), s.max()
            r_min, r_max = r.min(), r.max()
            v = 0.5
            
            vikor_score = pd.Series(index=self.filtered_devices, dtype=float)
            for d in self.filtered_devices:
                val_s = (s[d] - s_min) / (s_max - s_min) if s_max != s_min else 0
                val_r = (r[d] - r_min) / (r_max - r_min) if r_max != r_min else 0
                vikor_score[d] = v * val_s + (1 - v) * val_r
            scores.loc[self.filtered_devices] = 1.0 - vikor_score

        # 5. BUILD THE RESULT TABLE
        res = pd.DataFrame({"Score": scores})
        res["Status"] = ["Accepted" if i in self.filtered_devices else "Refuse" for i in res.index]
        res["Rank"] = res["Score"].rank(ascending=False, method="min")
        res.loc[res["Status"] == "Refuse", "Score"] = 0.0
        res.loc[res["Status"] == "Refuse", "Rank"] = float('nan')
        res = res.sort_values(by="Rank")
        
        # 6. STORE RESULTS IN SELF.RESULTS STRUCTURE
        self.results = {
            "method": method,
            "norm_method": norm_method,
            "weights": self.weights.copy(),
            "active_columns": active_cols,
            "active_weights": active_weights.copy(),
            "ranking": res,
            "sensitivity": self.sensitivity_results if hasattr(self, 'sensitivity_results') else None,
            "timestamp": pd.Timestamp.now()
        }
        
        return res

    def print_results(self):
        """
        Pretty-print the stored MCDA results from self.results.
        Displays method info, weights, ranking, and sensitivity bounds (if available).
        """
        if self.results is None:
            print("❌ No results stored. Run run_mcda() first!")
            return
        
        print("\n" + "=" * 90)
        print("   MCDA ANALYSIS RESULTS")
        print("=" * 90)
        
        print(f"\n📋 Configuration:")
        print(f"   MCDA Method:       {self.results['method']}")
        print(f"   Normalization:     {self.results['norm_method']}")
        print(f"   Timestamp:         {self.results['timestamp']}")
        print(f"   Active Criteria:   {len(self.results['active_columns'])} / {len(self.variables_config)}")
        
        print(f"\n📊 Used Weights (after filtering):")
        for col in self.results['active_columns']:
            full_name = self.variables_config.get(col, {}).get("full_name", col)
            w_value = self.results['active_weights'].get(col, 0.0)
            print(f"   • {col:20s} = {w_value:7.4f}  ({full_name})")
        
        print(f"\n🏆 Ranking Results:")
        ranking_df = self.results['ranking'][['Score', 'Status', 'Rank']].copy()
        print(ranking_df.to_string())
        
        # Display sensitivity bounds if available
        if self.results['sensitivity'] is not None:
            print(f"\n⚙️  Weight Stability Bounds (Sensitivity Analysis):")
            sens_df = self.results['sensitivity'][['w_min', 'w_max', 'delta_minus', 'delta_plus']].copy()
            print(sens_df.to_string())
        else:
            print(f"\n⚙️  Sensitivity analysis not yet performed.")
            print(f"   → Run: hta.find_stability_intervals() to compute weight bounds")
        
        print("\n" + "=" * 90 + "\n")

    def compare_approaches(self):
        """Compare result rankings across different normalization and MCDA method combinations."""
        combinations = [("minmax", "SAW"), ("minmax", "TOPSIS"), ("weitendorf", "SAW"), ("weitendorf", "TOPSIS"), ("z_score", "SAW"), ("z_score", "TOPSIS")]
        comparison_df = pd.DataFrame(index=self.devices)
        for norm, mcda in combinations:
            res = self.run_mcda(method=mcda, norm_method=norm)
            comparison_df[f"{norm}+{mcda}"] = res["Rank"]
            print("\n--- Compare of methodological concepts (Rank) ---")
            print(comparison_df.loc[self.filtered_devices])
            self.comparison = comparison_df
            
    def show_variables(self):
        """Print a structured list of short names, full names, and generation parameters."""
        print("\n" + "="*80)
        print("   VARIABLE OVERVIEW AND DATA GENERATOR SETTINGS")
        print("="*80)
        
        # Iterate through all variables in the configuration
        for short_name, cfg in self.variables_config.items():
            print(f"🔹 Short name: '{short_name}'")
            print(f"   - Full name:  {cfg.get('full_name', 'Not provided')}")
            print(f"   - Data type:  {cfg.get('dtype', 'float')} | Criterion direction: {cfg.get('type', 'benefit')}")
            
            # Display parameters depending on the data type
            if cfg.get("dtype") == "bool":
                print(f"   - Parameters:   Probability True = {cfg.get('prob_true', 0.5)*100}%")
            else:
                round_info = f" (rounded to {cfg['round_to']})" if "round_to" in cfg else ""
                print(f"   - Range (Min, Max): {cfg.get('range')}{round_info}")
                if "std" in cfg or "skewness" in cfg:
                    print(f"   - Distribution:  Std deviation = {cfg.get('std')}, Skewness = {cfg.get('skewness')}")
                else:
                    print(f"   - Distribution:  Uniform")
            print("-" * 80)

    def update_variable_config(self, short_name, new_settings, regenerate=True):
        """
        Update or add the configuration for a specific variable.
        :param short_name: Short name of the variable to edit or add (e.g. 'price').
        :param new_settings: Dictionary with new parameters (e.g. {'range': (100, 200), 'dtype': 'int'}).
        :param regenerate: If True, regenerate the full data matrix immediately so the changes take effect.
        """
        if short_name in self.variables_config:
            # Update existing settings
            self.variables_config[short_name].update(new_settings)
            print(f"\n🔄 Variable configuration for '{short_name}' was updated successfully.")
        else:
            # Add a completely new variable if the short name does not exist
            self.variables_config[short_name] = new_settings
            print(f"\n➕ A new variable '{short_name}' was added.")
            
        # Recalculate the total number of variables
        self.n_variables = len(self.variables_config)
        
        # If requested, regenerate the data immediately so the changes become effective
        if regenerate:
            self.generate_data()

    def find_stability_intervals(self, method="SAW", norm_method="weitendorf", max_iter=10, min_step=0.01):
        """
        Find the stability interval for each active weight using the bisection interval method.
        Updated: tests only columns that actually enter MCDA (those with variance).
        """
        if self.weights is None:
            self.set_weights({c: 1 for c in self.variables_config.keys()})
            
        # Suppress informational output during hundreds of rapid sensitivity-analysis iterations
        self._silence_info = True
            
        base_res = self.run_mcda(method=method, norm_method=norm_method)
        base_order = base_res[base_res["Status"] == "Accepted"]["Rank"].to_dict()
        
        # --- KEY CHANGE: Use only columns with real discriminating power ---
        active_cols = self._prepare_active_dimensions()
        
        intervals = {}
        original_weights = self.weights.copy()
        
        # Iterate only over active columns
        for target_var in active_cols:
            w_orig = original_weights[target_var]
            
            # --- FIND UPPER BOUND (w_max) ---
            low_w, high_w = w_orig, 1.0
            w_max = w_orig
            
            for _ in range(max_iter):
                if (high_w - low_w) < min_step: 
                    break
                test_w = (low_w + high_w) / 2
                
                new_weights = {target_var: test_w}
                rem = 1.0 - test_w
                denom = original_weights[active_cols].drop(target_var).sum()
                
                for ov in original_weights.keys():
                    if ov == target_var:
                        continue
                    if ov in active_cols:
                        new_weights[ov] = (original_weights[ov] / denom) * rem if denom > 0 else rem / (len(active_cols) - 1)
                    else:
                        new_weights[ov] = original_weights[ov] # Inactive columns (e.g., with weight 0) retain their original state
                
                self.weights = pd.Series(new_weights)
                test_res = self.run_mcda(method=method, norm_method=norm_method)
                test_order = test_res[test_res["Status"] == "Accepted"]["Rank"].to_dict()
                
                if test_order == base_order:
                    w_max = test_w
                    low_w = test_w
                else:
                    high_w = test_w
            
            # --- FIND LOWER BOUND (w_min) ---
            low_w, high_w = 0.0, w_orig
            w_min = w_orig
            
            for _ in range(max_iter):
                if (high_w - low_w) < min_step: 
                    break
                test_w = (low_w + high_w) / 2
                
                new_weights = {target_var: test_w}
                rem = 1.0 - test_w
                denom = original_weights[active_cols].drop(target_var).sum()
                
                for ov in original_weights.keys():
                    if ov == target_var:
                        continue
                    if ov in active_cols:
                        new_weights[ov] = (original_weights[ov] / denom) * rem if denom > 0 else rem / (len(active_cols) - 1)
                    else:
                        new_weights[ov] = original_weights[ov]
                        
                self.weights = pd.Series(new_weights)
                test_res = self.run_mcda(method=method, norm_method=norm_method)
                test_order = test_res[test_res["Status"] == "Accepted"]["Rank"].to_dict()
                
                if test_order == base_order:
                    w_min = test_w
                    high_w = test_w
                else:
                    low_w = test_w
            
            intervals[target_var] = {
                "current_weight": w_orig, 
                "w_min": w_min, 
                "w_max": w_max,
                "delta_minus": w_min - w_orig,
                "delta_plus": w_max - w_orig
            }
            
        # Restore original weights and exit silent mode
        self.weights = original_weights
        self._silence_info = False
        
        self.sensitivity_results = pd.DataFrame(intervals).T
        return self.sensitivity_results


    def plot_relative_stability_delta(self, method="SAW", norm_method="weitendorf", sort_by="range"):
        """
        Plot permissible relative weight shifts from the current baseline (0)
        using a symmetric logarithmic scale (SymLog).
        
        Effectively expands high-sensitivity micro-variations near zero,
        while simultaneously compressing macro-variations near +/- 1.0
        without scale distortion.
        """
        # Load stored sensitivity-analysis data
        df = self.find_stability_intervals(method=method, norm_method=norm_method).copy()
        df["total_range"] = df["w_max"] - df["w_min"]
        
        # Helper function to wrap long labels into two lines
        def wrap_label(text, max_chars=25):
            words = text.split()
            lines, current = [], ""
            for w in words:
                if len((current + " " + w).strip()) <= max_chars:
                    current = (current + " " + w).strip()
                else:
                    if current: lines.append(current)
                    current = w
            if current: lines.append(current)
            return "\n".join(lines)
            
        df["wrapped_name"] = [wrap_label(self.variables_config[c]["full_name"]) for c in df.index]
        
        # Sort by interval width
        if sort_by == "range":
            df = df.sort_values(by="total_range", ascending=False)
            
        labels = df["wrapped_name"].values
        delta_min = df["delta_minus"].values
        delta_max = df["delta_plus"].values
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # --- KEY CHANGE: Use a symmetric logarithmic scale ---
        # linthresh=0.1 means that the interval (-0.1, 0.1) stays linear and the logarithm begins only beyond it
        ax.set_xscale('symlog', linthresh=0.1)
        
        # Visually highlight the linear zone (gray background for fine details)
        ax.axvspan(-0.1, 0.1, color='gray', alpha=0.08, label='Linear zone (detail)')
        
        # Draw the zero center line (current setting)
        ax.axvline(x=0, color='black', linestyle='-', linewidth=1.5, label="Preset weight's setup")
        
        # Draw horizontal tolerance bars
        for idx, (d_min, d_max) in enumerate(zip(delta_min, delta_max)):
            ax.hlines(y=idx, xmin=d_min, xmax=d_max, color='#e74c3c', alpha=0.3, linewidth=10)
            ax.plot([d_min, d_max], [idx, idx], color='#c0392b', marker='|', markersize=12, markeredgewidth=2)
            
        # Set Y and X axis labels
        ax.set_yticks(np.arange(len(labels)))
        ax.set_yticklabels(labels, fontsize=9)
        
        # Nice formatting of X-axis markers (avoiding ugly exponents like 10^-1)
        ax.set_xticks([-1.0, -0.5, -0.2, -0.1, -0.05, 0, 0.05, 0.1, 0.2, 0.5, 1.0])
        ax.set_xticklabels(['-1.0', '-0.5', '-0.2', '-0.1', '-0.05', '0', '0.05', '0.1', '0.2', '0.5', '1.0'])
        
        ax.set_xlabel("Permissible Relative Weight Shift (Δ Delta)")
        ax.set_title(f"Weight Stability Bounds Prior to Rank Collapse\n(SymLog Scale | MCDA: {method} + {norm_method})", 
                     fontsize=11, fontweight='bold', pad=15)
        
        # Set axis limits with a small margin beyond the maximum possible range
        ax.set_xlim(-1.1, 1.1)
        
        ax.grid(True, linestyle='--', alpha=0.4, axis='x')
        ax.legend(loc='upper right')
        plt.tight_layout()
        plt.show()