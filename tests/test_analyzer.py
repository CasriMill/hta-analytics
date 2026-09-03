from hta.analyzer import HTA


def test_analyzer_generates_configured_devices():
    hta = HTA(n_devices=6)

    assert hta.raw_data is not None
    assert len(hta.devices) == 6
    assert set(hta.filtered_devices) == set(hta.devices)
    assert set(hta.variables_config).issubset(hta.raw_data.columns)


def test_analyzer_runs_mcda_and_returns_ranking():
    hta = HTA(n_devices=6)
    ranking = hta.run_mcda(method="SAW", norm_method="minmax")

    assert not ranking.empty
    assert {"Score", "Status", "Rank"}.issubset(ranking.columns)
    assert hta.results["method"] == "SAW"
    assert hta.results["norm_method"] == "minmax"
