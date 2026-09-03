import os

from hta.analyzer import HTA


def test_demo_data_ranking_stability():
    data_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "mcda_demo_data_weight_8devices.csv",
    )

    hta = HTA()
    hta.load_data(data_file)
    hta.set_weights({
        "price": 8,
        "efficiency": 10,
        "supplies": 5,
        "ce_cert": 0,
    })

    # Use same reference run as the demo workflow for regression guard.
    hta.apply_filters({"ce_cert": True})
    result = hta.run_mcda(method="SAW", norm_method="minmax")

    expected_ranking = [
        "Device_6",
        "Device_2",
        "Device_8",
        "Device_1",
        "Device_5",
        "Device_3",
        "Device_7",
    ]

    actual = result[result["Status"] == "Accepted"].index.tolist()
    assert actual == expected_ranking
