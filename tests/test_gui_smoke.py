from PySide6.QtWidgets import QApplication

from hta.gui_main import HTAGUI


def test_gui_can_initialize():
    app = QApplication.instance() or QApplication([])
    window = HTAGUI()
    assert window is not None
    assert window.hta is not None
    assert window.statusBar() is not None
    window.set_status("Testing status bar")
    assert "Testing status bar" in window.statusBar().currentMessage()
    assert [window.tabs.tabText(index) for index in range(window.tabs.count())] == [
        "Weights",
        "Filters",
        "rw_data",
        "Results",
        "Graphs",
    ]
    assert window.chart_panel.ranking_canvas is not None
    assert window.chart_panel.sensitivity_canvas is not None
    window.close()
