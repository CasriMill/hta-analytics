import pandas as pd
import pytest

from hta.analyzer import HTA


def test_apply_filters_supports_bool_and_numeric_rules():
    hta = HTA(n_devices=20)
    hta.apply_filters([
        {"column": "ce_cert", "operator": "eq", "value": True},
        {"column": "price", "operator": "lte", "value": hta.raw_data["price"].max()},
    ])

    assert len(hta.filtered_devices) > 0
    assert set(hta.filtered_devices).issubset(set(hta.devices))


def test_apply_filters_supports_between_rule():
    hta = HTA(n_devices=20)
    lower = float(hta.raw_data["efficacy"].min())
    upper = float(hta.raw_data["efficacy"].max())

    hta.apply_filters([
        {"column": "efficacy", "operator": "between", "lower": lower, "upper": upper},
    ])

    assert len(hta.filtered_devices) == len(hta.devices)


def test_export_results_csv_creates_file(tmp_path):
    hta = HTA(n_devices=10)
    hta.apply_filters({"ce_cert": True})
    result = hta.run_mcda(method="SAW", norm_method="minmax")

    output_path = tmp_path / "results.csv"
    hta.export_results(output_path)

    assert output_path.exists()
    exported = pd.read_csv(output_path, index_col=0)
    assert list(exported.columns) == ["Score", "Status", "Rank"]
    assert len(exported) == len(result)


def test_export_results_xlsx_creates_file(tmp_path):
    pytest.importorskip("openpyxl")

    hta = HTA(n_devices=10)
    hta.apply_filters({"ce_cert": True})
    hta.run_mcda(method="SAW", norm_method="minmax")

    output_path = tmp_path / "results.xlsx"
    hta.export_results(output_path)

    assert output_path.exists()
