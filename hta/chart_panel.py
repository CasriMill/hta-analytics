from __future__ import annotations

import numpy as np

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
        self.sensitivity_scope = QLabel("Sensitivity intervals are valid only for the current dataset and active filters.")

        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addWidget(self.sensitivity_scope)
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
                positions = np.arange(len(labels))
                for position, (_, values) in zip(positions, sensitivity.iterrows()):
                    lower = float(values["w_min"])
                    current = float(values["current_weight"])
                    upper = float(values["w_max"])
                    self.sensitivity_ax.plot(
                        [lower, upper], [position, position],
                        color="#27AE60", linewidth=10, solid_capstyle="butt",
                    )
                    self.sensitivity_ax.plot(
                        current, position, marker="|", markersize=18,
                        markeredgewidth=2, color="#1B4D3E",
                    )
                    self.sensitivity_ax.annotate(
                        f"{lower:.3f}", (lower, position), xytext=(-4, 9),
                        textcoords="offset points", ha="right", va="bottom", fontsize=8,
                    )
                    self.sensitivity_ax.annotate(
                        f"{upper:.3f}", (upper, position), xytext=(4, 9),
                        textcoords="offset points", ha="left", va="bottom", fontsize=8,
                    )
                    self.sensitivity_ax.annotate(
                        f"{current:.3f}", (current, position), xytext=(0, -14),
                        textcoords="offset points", ha="center", va="top", fontsize=8,
                        color="#1B4D3E",
                    )
                self.sensitivity_ax.set_yticks(positions)
                self.sensitivity_ax.set_yticklabels(labels)
                self.sensitivity_ax.set_xlabel("Weight")
                self.sensitivity_ax.set_title(
                    f"Weight sensitivity\n{hta.dataset_label}; "
                    f"{len(hta.filtered_devices)} of {len(hta.devices)} devices"
                )
                self.sensitivity_ax.tick_params(axis="y", labelsize=8)
            except Exception:
                self.sensitivity_ax.text(0.5, 0.5, "Sensitivity unavailable", ha="center", va="center")

        self.ranking_figure.tight_layout()
        self.sensitivity_figure.tight_layout()
        self.ranking_canvas.draw()
        self.sensitivity_canvas.draw()
