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


def test_import_protocol_tracks_invalid_numeric_rows_and_categories(tmp_path):
    source = tmp_path / "invalid.csv"
    source.write_text(
        "Device_ID;score;approved;category\n"
        "HTA_Type;benefit;benefit;benefit\n"
        "HTA_Dtype;int;bool;category\n"
        "HTA_Weight;1;0;0\n"
        "Device_1;10;True;1\n"
        "Device_2;bad;False;2\n",
        encoding="utf-8",
    )

    hta = HTA()

    assert hta.load_data(str(source))
    assert hta.devices == ["Device_1"]
    assert "category" in hta.variables_config
    assert hta.variables_config["category"]["dtype"] == "category"
    assert hta.import_dropped_devices == ["Device_2"]
    assert hta.import_validation_issues


@pytest.mark.parametrize("method", [
    "weitendorf", "minmax", "max", "juttler", "juttler_korth",
    "sum", "vector", "sigmoid", "peldchus",
])
def test_normalization_methods_make_higher_values_better(method):
    hta = HTA(n_devices=10)
    hta.raw_data = pd.DataFrame({
        "benefit": [1.0, 2.0, 4.0],
        "cost": [1.0, 2.0, 4.0],
    }, index=["a", "b", "c"])
    hta.devices = ["a", "b", "c"]
    hta.variables_config = {
        "benefit": {"type": "benefit", "dtype": "float"},
        "cost": {"type": "cost", "dtype": "float"},
    }

    normalized = hta.normalize_data(method=method, peldchus_t=2)

    assert normalized["benefit"].is_monotonic_increasing
    assert normalized["cost"].is_monotonic_decreasing


def test_sigmoid_uses_median_and_iqr():
    hta = HTA(n_devices=3)
    hta.raw_data = pd.DataFrame({"cost": [1.0, 2.0, 4.0]}, index=["a", "b", "c"])
    hta.devices = ["a", "b", "c"]
    hta.variables_config = {"cost": {"type": "cost", "dtype": "float"}}

    normalized = hta.normalize_data(method="sigmoid")["cost"]

    assert normalized.loc["b"] == pytest.approx(0.5)
    assert normalized.loc["a"] > normalized.loc["c"]


def test_peldchus_t_one_matches_weitendorf():
    hta = HTA(n_devices=3)
    hta.raw_data = pd.DataFrame({"benefit": [1.0, 2.0, 4.0]}, index=["a", "b", "c"])
    hta.devices = ["a", "b", "c"]
    hta.variables_config = {"benefit": {"type": "benefit", "dtype": "float"}}

    weitendorf = hta.normalize_data(method="weitendorf")["benefit"]
    peldchus = hta.normalize_data(method="peldchus", peldchus_t=1)["benefit"]

    pd.testing.assert_series_equal(weitendorf, peldchus)
