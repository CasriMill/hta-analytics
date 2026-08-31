# -*- coding: utf-8 -*-
"""
Created on Sat Aug 29 21:03:19 2026

@author: millek
"""

from hta import HTA

        
# =====================================================================
# SPUŠTĚNÍ ANALÝZY A POROVNÁNÍ METOD (Vložte na konec souboru)
# =====================================================================
if __name__ == "__main__":
    # 1. Inicializace pro 6 zařízení (vygeneruje data v pozadí)
    hta = HTA(n_devices=16)
    # hta = HTA(n_devices=None)
    # hta.load_data('mcda_data.csv')
    hta.show_variables()
    
    print("--- SUROVÁ SIMULOVANÁ DATA ---")
    print(hta.raw_data)
    
    # 2. Vykreslení popisné statistiky a Boxplotů pro číselné proměnné
    hta.plot_descriptive_stats()
    
    # 3. Zadání libovolných ne-normalizovaných vah (např. body 1 až 10)
    # # Třída si je sama přepočítá, aby v součtu dávaly 100 % (1.0)
    vahy_body = {
        "price": 3.5,
        "op_costs": 2.1,
        "efficacy": 0.5,
        "consumables": 2.55,
        "training": 0.25,
        "accuracy": 0.15,
        "service_life": 0.125,
        "connectivity_eth": 0.25,
        "connectivity_wifi": 0.25,
        "connectivity_usb": 0.025,
        "protocol_hl7": 0.05,
        "connectivity_his": 0.25,
        "ce_cert": 0.00
    }
    print("Součet vah: " + str(sum(vahy_body.values())))
    hta.set_weights(vahy_body)
    
    # 4. Aplikace VYŘAZUJÍCÍHO kritéria (CE certifikace musí být striktně True)
    hta.apply_filters({"ce_cert": True})
    
    # 5. Spuštění vaší oblíbené kombinace (Weitendorf normalizace + SAW)
    print("\n--- VÝSLEDEK HODNOCENÍ: WEITENDORF + TOPSIS ---")
    vysledek = hta.run_mcda(method="TOPSIS", norm_method="weitendorf")
    print(vysledek)
    
    # 6. Spuštění exaktní CITLIVOSTNÍ ANALÝZY 
    hta.plot_relative_stability_delta(method="TOPSIS", norm_method="weitendorf", sort_by="range")
    print("\n--- ULOŽENÉ VÝSLEDKY CITLIVOSTNÍ ANALÝZY V ATRIBUTU ---")
    print(hta.sensitivity_results[["current_weight", "delta_minus", "delta_plus"]].round(3))
    
    # 7. POROVNÁNÍ METODOLOGICKÝCH PŘÍSTUPŮ (Vliv normalizace a MCDA na pořadí)
    hta.compare_approaches()            
    