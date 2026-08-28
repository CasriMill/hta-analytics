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
:version:     0.1.5
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
        
        # Slovník konfigurace začíná jako prázdný (pokud uživatel nedodá vlastní)
        # Kompletně se naplní dynamicky z meta-řádků načteného souboru
        self.variables_config = {} if variables_config is None else variables_config
            
        self.raw_data = None
        self.weights = None
        self.normalized_data = None
        self._silence_info = False
        
        # Pokud uživatel přesto zadá počet zařízení (generování na zelené louce), 
        # použijeme původní výchozí anglicko-český slovník
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
            Device_1;3500000;85.5;2;True
            Device_2;2800000;72.0;5;False
        
        """
        print(f"\n📂 Reading international HTA data from file: {file_path}")
        try:
            # Načtení souboru (automatická detekce oddělovače u CSV)
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, index_col=0, sep=None, engine='python')
            elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                df = pd.read_excel(file_path, index_col=0)
            else:
                raise ValueError("Unsupported file format. Use .csv or .xlsx with sep=';' and decimal = '.'!")
            
            # --- EXTRAKCE METADAT Z HLAVIČKY SOUBORU ---
            types_row = df.loc["HTA_Type"]
            dtypes_row = df.loc["HTA_Dtype"]
            
            # Ošetření: full_name řádek je volitelný, pokud chybí, použijeme zkrácený název
            if "HTA_FullName" in df.index:
                full_names_row = df.loc["HTA_FullName"]
                rows_to_drop = ["HTA_Type", "HTA_Dtype", "HTA_FullName"]
            else:
                full_names_row = None
                rows_to_drop = ["HTA_Type", "HTA_Dtype"]
            
            # Dynamické sestavení vnitřního variables_config slovníku
            self.variables_config = {}
            for col in df.columns:
                self.variables_config[col] = {
                    "type": str(types_row[col]).strip().lower(),
                    "dtype": str(dtypes_row[col]).strip().lower(),
                    "full_name": str(full_names_row[col]).strip() if full_names_row is not None else str(col)
                }
            
            # --- CLEAN DATA w/o METADATA ---
            # drop of comments and confi rows
            self.raw_data = df.drop(rows_to_drop)
            
            # Přetypování sloupců podle načtených parametrů
            for col in self.raw_data.columns:
                dt = self.variables_config[col]["dtype"]
                if dt == "int":
                    self.raw_data[col] = pd.to_numeric(self.raw_data[col]).round().astype(int)
                elif dt == "float":
                    self.raw_data[col] = pd.to_numeric(self.raw_data[col]).astype(float)
                elif dt == "bool":
                    # Převede texty 'True'/'False' nebo čísla 1/0 správně na čistý boolean typu bool
                    self.raw_data[col] = self.raw_data[col].map({'True': True, 'False': False, 1: True, 0: False, True: True, False: False})
            
            # Nastavení vnitřních proměnných třídy podle reálných dat
            self.devices = list(self.raw_data.index)
            self.filtered_devices = list(self.devices)
            self.n_devices = len(self.devices)
            
            print(f"✅ Succesfull import of {self.n_devices} devices.")
            
            # Spuštění testu konzistence dat (ověří, zda v souboru nejsou NaN nebo chyby)
            return self.validate_data()
            
        except Exception as e:
            print(f"❌ Critical error in import of file: {str(e)}")
            self.raw_data = None
            return False


    def generate_data(self):
        """Vygeneruje surová simulovaná data a aplikuje provázání nejdražšího přístroje se školením/přesností."""
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
            data[short_name] = gen_arr.astype(int) if dtype == "int" else gen_arr
                
        self.raw_data = pd.DataFrame(data, index=self.devices)
        
        # --- ZAVEDENÍ ZÁVISLOSTI (Korelace s cenou) ---
        self.raw_data = self.raw_data.sort_values(by="cena", ascending=True)
        if "skoleni" in self.raw_data.columns:
            self.raw_data["skoleni"] = np.sort(self.raw_data["skoleni"].values)
        if "presnost" in self.raw_data.columns:
            self.raw_data["presnost"] = np.sort(self.raw_data["presnost"].values)
        self.raw_data = self.raw_data.sort_index()
        
        return self.raw_data

    def validate_data(self):
        """ Provede striktní kontrolu formátu a konzistence načtených nebo vygenerovaných dat. """
        if self.raw_data is None:
            print("❌ Kritická chyba: Nejsou načtena žádná data ke kontrole.")
            return False
            
        is_consistent = True
        print("\n🔍 SPUŠTĚN TEST KONZISTENCE A FORMÁTU DAT...")
        
        if self.raw_data.isna().sum().sum() > 0:
            print("   ⚠️ Pozor: Tabulka obsahuje prázdné nebo nedefinované hodnoty (NaN)!")
            is_consistent = False
            
        for short_name in self.variables_config.keys():
            if short_name not in self.raw_data.columns:
                print(f"   ❌ Kritická chyba: V datech kompletně chybí vyžadovaný sloupec '{short_name}'!")
                is_consistent = False
                continue
                
            cfg = self.variables_config[short_name]
            series = self.raw_data[short_name]
            dtype = cfg.get("dtype", "float")
            
            if dtype == "bool":
                if not series.isin([True, False, 0, 1, 0.0, 1.0]).all():
                    print(f"   ❌ Chyba typu: Sloupec '{short_name}' má být typu BOOL, ale obsahuje jiná data!")
                    is_consistent = False
            elif dtype == "int":
                if not np.equal(series, series.astype(int)).all():
                    print(f"   ⚠️ Varování: Sloupec '{short_name}' má být INT, ale obsahuje desetinná čísla!")
                    
            if dtype != "bool" and "range" in cfg:
                low, high = cfg["range"]
                if series.min() < low or series.max() > high:
                    print(f"   ⚠️ Varování rozmezí: Hodnoty ve sloupci '{short_name}' utíkají mimo konfiguraci (Aktuální Min: {series.min()}, Max: {series.max()} vs povolené {cfg['range']}).")

        if is_consistent:
            print("🚀 Všechny testy formátu a konzistence proběhly úspěšně. Data jsou validní.")
        else:
            print("⚠️ V datech byly nalezeny nesrovnalosti. Zkontrolujte výpis výše.")
            
        return is_consistent


    def generate_data(self):
        """Vygeneruje surová data a zajistí, aby nejdražší přístroje měly nejdražší školení/přesnost."""
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
                
        # Vytvoření základního DataFrame
        self.raw_data = pd.DataFrame(data, index=self.devices)
        
        # =====================================================================
        # ZAVEDENÍ ZÁVISLOSTI (Korelace s cenou)
        # =====================================================================
        # 1. Seřadíme celý DataFrame podle ceny vzestupně (od nejlevnějšího po nejdražší)
        self.raw_data = self.raw_data.sort_values(by="price", ascending=True)
        
        # 2. Pokud existuje proměnná pro školení, vezmeme její hodnoty, seřadíme je a přepíšeme je zpět
        # Tím zajistíme: nejlevnější přístroj = nejlevnější školení, nejdražší přístroj = nejdražší školení
        if "training" in self.raw_data.columns:
            self.raw_data["training"] = np.sort(self.raw_data["training"].values)
            
        # 3. Totéž provedeme pro přesnost (pokud ji máte v systému definovanou)
        if "accuracy" in self.raw_data.columns:
            self.raw_data["accuracy"] = np.sort(self.raw_data["accuracy"].values)
            
        # Optional: Na konci vrátíme indexy zpět do původního pořadí (Device_1, Device_2...), 
        # aby řádky nebyly vizuálně přeházené, ale hodnoty uvnitř už zůstanou perfektně svázané.
        self.raw_data = self.raw_data.sort_index()
        
        return self.raw_data


    def plot_descriptive_stats(self, cols_per_row=3):
        """
        Vypíše popisnou statistiku a vykreslí kombinovaný Violin + Scatter plot
        uspořádaný přehledně do více řádků.
        :param cols_per_row: Maximální počet grafů (sloupců) na jednom řádku.
        """
        numeric_cols = [c for c, cfg in self.variables_config.items() if cfg.get("dtype") != "bool"]
        n_plots = len(numeric_cols)
        
        print("\n--- Descriptive statistics imported data ---")
        stats_df = self.raw_data[numeric_cols].describe().T
        stats_df["full_name"] = [self.variables_config[c]["full_name"] for c in numeric_cols]
        print(stats_df[["full_name", "count", "mean", "std", "min", "max"]])
        
        # Výpočet potřebného počtu řádků v mřížce
        n_rows = (n_plots + cols_per_row - 1) // cols_per_row
        
        # Dynamické určení velikosti okna podle počtu řádků a sloupců
        fig, axes = plt.subplots(n_rows, cols_per_row, figsize=(4 * cols_per_row, 4.5 * n_rows))
        
        # Převedeme axes na jednorozměrné pole pro snadnější indexaci (i v případě 1x1 nebo 1xN)
        if n_plots == 1:
            axes = np.array([axes])
        else:
            axes = axes.flatten()
            
        for i, col in enumerate(numeric_cols):
            ax = axes[i]
            data_to_plot = self.raw_data[col].values
            
            # 1. Vykreslení Violin plotu
            parts = ax.violinplot(data_to_plot, showmeans=False, showmedians=True, showextrema=True)
            
            # Úprava vzhledu violinu
            for pc in parts['bodies']:
                pc.set_facecolor('#1f77b4')
                pc.set_edgecolor('grey')
                pc.set_alpha(0.6)
            parts['cmedians'].set_color('black')
            parts['cmaxes'].set_color('grey')
            parts['cmins'].set_color('grey')
            
            # 2. Vykreslení Scatter plotu s jitterem (červené body)
            jitter = np.random.normal(1, 0.04, size=len(data_to_plot))
            ax.scatter(jitter, data_to_plot, color='red', alpha=0.7, edgecolors='black', zorder=3)
            
            # Popisky a formátování jednotlivého sub-grafu
            ax.set_title(self.variables_config[col]["full_name"], fontsize=9, pad=10)
            ax.set_xticks([1])
            ax.set_xticklabels(["Distribuce"])
            ax.grid(True, linestyle='--', alpha=0.5)
            
        # 3. Skrytí nevyužitých (prázdných) pod-grafů v mřížce
        for j in range(i + 1, len(axes)):
            fig.delaxes(axes[j])
            
        plt.tight_layout()
        plt.show()



    def set_weights(self, weights_dict):
        """Normalizuje libovolné váhy tak, aby součet byl 1.0."""
        full_weights = {v: weights_dict.get(v, 0.0) for v in self.variables_config.keys()}
        total = sum(full_weights.values())
        if total <= 0: raise ValueError("Součet vah nesmí být <=0!")
        self.weights = pd.Series({k: v / total for k, v in full_weights.items()})
        return self.weights

    def apply_filters(self, filter_dict):
        """Uplatní vyřazující kritéria (např. {'ce_cert': True})."""
        self.filtered_devices = list(self.devices)
        for col, target_val in filter_dict.items():
            if col in self.raw_data.columns:
                passed = self.raw_data[self.raw_data[col] == target_val].index
                self.filtered_devices = [d for d in self.filtered_devices if d in passed]
        print(f"\nFiltr {filter_dict} uplatněn. Postupuje {len(self.filtered_devices)} z {self.n_devices} zařízení.")

    def normalize_data(self, method="weitendorf"):
        """Variantní normalizace dat: 'minmax', 'weitendorf', "z_score"."""
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
            # Získáme surová data pouze pro zařízení, která prošla filtrem
            raw_series = self.raw_data.loc[self.filtered_devices, col]
            
            # Pokud je ve sloupci více než 1 unikátní hodnota, sloupec je užitečný pro MCDA
            if raw_series.nunique() > 1:
                active_cols.append(col)
            else:
                # Informujeme uživatele, že sloupec byl povýšen čistě na vyřazující filtr
                # (Vypíše se pouze pokud měl nastavenou nenulovou váhu)
                if self.weights is not None and self.weights.get(col, 0) > 0:
                    # Tuto zprávu vypíšeme jen při reálném výpočtu, při citlivostce (kdy se váhy neustále mění) ji skryjeme
                    if hasattr(self, '_silence_info') and not self._silence_info:
                        print(f"ℹ️ Kritérium '{col}' slouží v tomto kontextu pouze jako filtr (všechna schválená zařízení mají shodnou hodnotu).")
        return active_cols

    def _adjust_active_weights(self, active_cols):
        """
        KROK 2: Test a přepočet vah.
        Vezme původní váhy, vyřadí neaktivní sloupce a zbylé váhy znormalizuje na 1.0.
        """
        if self.weights is None:
            self.set_weights({c: 1 for c in self.variables_config.keys()})
            
        # Vytáhneme váhy pouze pro užitečné sloupce
        active_weights = self.weights[active_cols].copy()
        
        # Provedeme přepočet (redistribuci) tak, aby součet aktivních vah dával přesně 1.0 (100 %)
        if active_weights.sum() > 0:
            active_weights = active_weights / active_weights.sum()
        else:
            # Krajní případ: Pokud by nezbyla žádná váha, rozdělíme důležitost rovnoměrně
            active_weights = pd.Series(1.0 / len(active_cols), index=active_cols)
            
        return active_weights

    def run_mcda(self, method="SAW", norm_method="minmax"):
        """
        KROK 3: Hlavní spouštěcí metoda MCDA realizující čistou analytickou pipeline:
        Očištění dimenzí -> Přepočet vah -> Normalizace -> Výpočet algoritmu.
        """
        # Inicializace výchozích vah, pokud ještě nebyly nastaveny
        if self.weights is None:
            self.set_weights({c: 1 for c in self.variables_config.keys()})
            
        # 1. ANALÝZA SLUPCŮ: Najdeme proměnné, které mají reálnou rozlišovací schopnost
        active_cols = self._prepare_active_dimensions()
        
        # 2. PŘEPOČET VAH: Očistíme váhy od netečných kritérií a vrátíme sumu na 100%
        active_weights = self._adjust_active_weights(active_cols)
        
        # 3. NORMALIZACE: Spustíme variantní normalizaci nad surovými daty
        self.normalize_data(method=norm_method)
        
        # Vybereme ze znormalizované matice pouze schválená zařízení a pouze aktivní sloupce
        active_matrix = self.normalized_data.loc[self.filtered_devices, active_cols].copy()
        
        # Příprava prázdné výsledné řady pro uložení skóre
        scores = pd.Series(0.0, index=self.devices)
        
        # 4. VÝPOČET MCDA METODY (Nyní pracuje s garantovanou čistou maticí a vahami)
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

        # 5. SESTAVENÍ VÝSLEDNÉ TABULKY
        res = pd.DataFrame({"Score": scores})
        res["Status"] = ["Accepted" if i in self.filtered_devices else "Refuse" for i in res.index]
        res["Rank"] = res["Score"].rank(ascending=False, method="min").astype(int)
        res.loc[res["Status"] == "Refuse", "Rank"] = 999
        return res.sort_values(by="Rank")

    def compare_approaches(self):
        """Porovná výsledné žebříčky různých kombinací normalizace a MCDA metod."""
        combinations = [("minmax", "SAW"), ("minmax", "TOPSIS"), ("weitendorf", "SAW"), ("weitendorf", "TOPSIS"), ("z_score", "SAW"), ("z_score", "TOPSIS")]
        comparison_df = pd.DataFrame(index=self.devices)
        for norm, mcda in combinations:
            res = self.run_mcda(method=mcda, norm_method=norm)
            comparison_df[f"{norm}+{mcda}"] = res["Rank"]
            print("\n--- Compare of methodological concepts (Rank) ---")
            print(comparison_df.loc[self.filtered_devices])
            self.comparison = comparison_df
            
    def show_variables(self):
        """ Vypíše přehledný seznam zkrácených názvů, plných názvů a parametrů generování. """
        print("\n" + "="*80)
        print("   PŘEHLED PROMĚNNÝCH A NASTAVENÍ GENERATORU DAT")
        print("="*80)
        
        # Projdeme všechny proměnné v konfiguraci
        for short_name, cfg in self.variables_config.items():
            print(f"🔹 Zkrácený název: '{short_name}'")
            print(f"   - Plný název:  {cfg.get('full_name', 'Není zadán')}")
            print(f"   - Datový typ:  {cfg.get('dtype', 'float')} | Směr kritéria: {cfg.get('type', 'benefit')}")
            
            # Zobrazení parametrů podle typu dat
            if cfg.get("dtype") == "bool":
                print(f"   - Parametry:   Pravděpodobnost True = {cfg.get('prob_true', 0.5)*100}%")
            else:
                round_info = f" (zaokr. na {cfg['round_to']})" if "round_to" in cfg else ""
                print(f"   - Rozsah (Min, Max): {cfg.get('range')}{round_info}")
                if "std" in cfg or "skewness" in cfg:
                    print(f"   - Distribuce:  Směrodatná odchylka (std) = {cfg.get('std')}, Šikmost (skewness) = {cfg.get('skewness')}")
                else:
                    print(f"   - Distribuce:  Rovnoměrná (Uniform)")
            print("-" * 80)

    def update_variable_config(self, short_name, new_settings, regenerate=True):
        """
        Změní nebo přidá konfiguraci konkrétní proměnné.
        :param short_name: Zkrácený název měněné/nové proměnné (např. 'cena').
        :param new_settings: Slovník s novými parametry (např. {'range': (100, 200), 'dtype': 'int'}).
        :param regenerate: Pokud je True, automaticky se znovu vygeneruje celá matice dat.
        """
        if short_name in self.variables_config:
            # Aktualizujeme stávající nastavení
            self.variables_config[short_name].update(new_settings)
            print(f"\n🔄 Konfigurace proměnné '{short_name}' byla úspěšně upravena.")
        else:
            # Pokud zkrácený název neexistuje, vytvoříme novou proměnnou
            self.variables_config[short_name] = new_settings
            print(f"\n➕ Byla přidána úplně nová proměnná '{short_name}'.")
            
        # Přepočítáme celkový počet proměnných
        self.n_variables = len(self.variables_config)
        
        # Pokud je požadováno, rovnou přegenerujeme data, aby se změny projevily
        if regenerate:
            self.generate_data()

    def find_stability_intervals(self, method="SAW", norm_method="weitendorf", max_iter=10, min_step=0.01):
        """
        Najde interval stability pro každou aktivní váhu pomocí algoritmu půlení intervalu.
        NOVĚ: Testuje POUZE sloupce, které reálně vstupují do MCDA (obsahují variabilitu).
        """
        if self.weights is None:
            self.set_weights({c: 1 for c in self.variables_config.keys()})
            
        # Potlačíme vypisování informačních hlášek během stovek rychlých iterací citlivostky
        self._silence_info = True
            
        base_res = self.run_mcda(method=method, norm_method=norm_method)
        base_order = base_res[base_res["Status"] == "Accepted"]["Rank"].to_dict()
        
        # --- KLÍČOVÁ ZMĚNA: Získáme pouze ty sloupce, které mají rozlišovací schopnost ---
        active_cols = self._prepare_active_dimensions()
        
        intervals = {}
        original_weights = self.weights.copy()
        
        # Iterujeme POUZE přes aktivní sloupce
        for target_var in active_cols:
            w_orig = original_weights[target_var]
            
            # --- HLEDÁNÍ HORNÍ HRANICE (w_max) ---
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
                        new_weights[ov] = original_weights[ov] # Vyřazeným sloupcům (např. s váhou 0) ponecháme původní stav
                
                self.weights = pd.Series(new_weights)
                test_res = self.run_mcda(method=method, norm_method=norm_method)
                test_order = test_res[test_res["Status"] == "Accepted"]["Rank"].to_dict()
                
                if test_order == base_order:
                    w_max = test_w
                    low_w = test_w
                else:
                    high_w = test_w
            
            # --- HLEDÁNÍ SPODNÍ HRANICE (w_min) ---
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
            
        # Obnovíme původní váhy a vypneme tichý režim
        self.weights = original_weights
        self._silence_info = False
        
        self.sensitivity_results = pd.DataFrame(intervals).T
        return self.sensitivity_results


    def plot_relative_stability_delta(self, method="SAW", norm_method="weitendorf", sort_by="range"):
        """
        Plot permissible relative weight shifts from the current baseline (0) 
        using a symmetric logarithmic scale (SymLog).
        
        Effectively expands high-sensitivity micro-variations near zero 
        while simultaneously compressing macro-variations near +/- 1.0 
        without scale distortion.
        """
        # Načteme uložená data citlivostní analýzy
        df = self.find_stability_intervals(method=method, norm_method=norm_method).copy()
        df["total_range"] = df["w_max"] - df["w_min"]
        
        # Pomocná funkce pro zalamování dlouhých popisků na dva řádky
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
        
        # Seřazení podle šířky intervalu
        if sort_by == "range":
            df = df.sort_values(by="total_range", ascending=False)
            
        labels = df["wrapped_name"].values
        delta_min = df["delta_minus"].values
        delta_max = df["delta_plus"].values
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # --- KLÍČOVÁ ZMĚNA: Nastavení symetrické logaritmické osy ---
        # linthresh=0.1 říká, že interval (-0.1, 0.1) bude lineární a teprve za ním začne logaritmus
        ax.set_xscale('symlog', linthresh=0.1)
        
        # Vizuální zvýraznění lineární zóny (šedé pozadí pro jemné detaily)
        ax.axvspan(-0.1, 0.1, color='gray', alpha=0.08, label='Linear zone (detail)')
        
        # Vykreslení nulové středové linie (aktuální nastavení)
        ax.axvline(x=0, color='black', linestyle='-', linewidth=1.5, label="Preset weight's setup")
        
        # Vykreslení horizontálních pruhů tolerancí
        for idx, (d_min, d_max) in enumerate(zip(delta_min, delta_max)):
            ax.hlines(y=idx, xmin=d_min, xmax=d_max, color='#e74c3c', alpha=0.3, linewidth=10)
            ax.plot([d_min, d_max], [idx, idx], color='#c0392b', marker='|', markersize=12, markeredgewidth=2)
            
        # Nastavení popisků osy Y a X
        ax.set_yticks(np.arange(len(labels)))
        ax.set_yticklabels(labels, fontsize=9)
        
        # Hezké formátování značek na ose X (aby tam nebyly ošklivé mocniny typu 10^-1)
        ax.set_xticks([-1.0, -0.5, -0.2, -0.1, -0.05, 0, 0.05, 0.1, 0.2, 0.5, 1.0])
        ax.set_xticklabels(['-1.0', '-0.5', '-0.2', '-0.1', '-0.05', '0', '0.05', '0.1', '0.2', '0.5', '1.0'])
        
        ax.set_xlabel("Permissible Relative Weight Shift (Δ Delta)")
        ax.set_title(f"Weight Stability Bounds Prior to Rank Collapse\n(SymLog Scale | MCDA: {method} + {norm_method})", 
                     fontsize=11, fontweight='bold', pad=15)
        
        # Nastavení limitů osy s drobnou rezervou za maximální možný rozsah
        ax.set_xlim(-1.1, 1.1)
        
        ax.grid(True, linestyle='--', alpha=0.4, axis='x')
        ax.legend(loc='upper right')
        plt.tight_layout()
        plt.show()