from __future__ import annotations

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget


class ChartPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.ranking_figure = Figure(figsize=(5, 3), dpi=100)
        self.ranking_ax = self.ranking_figure.add_subplot(111)
        self.ranking_canvas = FigureCanvasQTAgg(self.ranking_figure)
        self.sensitivity_figure = Figure(figsize=(5, 3), dpi=100)
        self.sensitivity_ax = self.sensitivity_figure.add_subplot(111)
        self.sensitivity_canvas = FigureCanvasQTAgg(self.sensitivity_figure)
        self.title = QLabel("Ranking and sensitivity analysis")

        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        charts = QHBoxLayout()
        charts.addWidget(self.ranking_canvas)
        charts.addWidget(self.sensitivity_canvas)
        layout.addLayout(charts)

    def update_chart(self, hta):
        self.ranking_ax.clear()
        self.sensitivity_ax.clear()
        if hta.results is None or hta.results.get("ranking") is None:
            self.ranking_ax.text(0.5, 0.5, "No results", ha="center", va="center")
            self.sensitivity_ax.text(0.5, 0.5, "No results", ha="center", va="center")
        else:
            ranking = hta.results["ranking"].copy()
            accepted = ranking[ranking["Status"] == "Accepted"].sort_values("Rank")
            if accepted.empty:
                self.ranking_ax.text(0.5, 0.5, "No accepted devices", ha="center", va="center")
            else:
                self.ranking_ax.barh(accepted.index, accepted["Score"].astype(float), color="#2E86DE")
                self.ranking_ax.invert_yaxis()
                self.ranking_ax.set_xlabel("Score")
                self.ranking_ax.set_title("Ranking")

            try:
                sensitivity = hta.find_stability_intervals(
                    method=hta.results.get("method", "SAW"),
                    norm_method=hta.results.get("norm_method", "weitendorf"),
                ).copy()
                if sensitivity.empty:
                    raise ValueError("No active criteria")
                sensitivity["range"] = sensitivity["w_max"] - sensitivity["w_min"]
                sensitivity = sensitivity.sort_values("range")
                labels = list(sensitivity.index)
                self.sensitivity_ax.barh(
                    labels,
                    sensitivity["w_max"] - sensitivity["current_weight"],
                    left=sensitivity["current_weight"],
                    color="#27AE60",
                    label="Allowed range",
                )
                self.sensitivity_ax.axvline(0, color="#555", linewidth=0.8)
                self.sensitivity_ax.set_xlabel("Weight")
                self.sensitivity_ax.set_title("Weight sensitivity")
                self.sensitivity_ax.tick_params(axis="y", labelsize=8)
            except Exception:
                self.sensitivity_ax.text(0.5, 0.5, "Sensitivity unavailable", ha="center", va="center")

        self.ranking_figure.tight_layout()
        self.sensitivity_figure.tight_layout()
        self.ranking_canvas.draw()
        self.sensitivity_canvas.draw()
