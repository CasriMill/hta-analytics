from __future__ import annotations

import numpy as np

from PySide6.QtCore import Signal
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class ChartPanel(QWidget):
    export_requested = Signal(str)

    def __init__(self):
        super().__init__()
        self.ranking_figure = Figure(figsize=(8, 5), dpi=100)
        self.ranking_ax = self.ranking_figure.add_subplot(111)
        self.ranking_canvas = FigureCanvasQTAgg(self.ranking_figure)
        self.sensitivity_figure = Figure(figsize=(8, 5), dpi=100)
        self.sensitivity_ax = self.sensitivity_figure.add_subplot(111)
        self.sensitivity_canvas = FigureCanvasQTAgg(self.sensitivity_figure)
        self.relative_sensitivity_figure = Figure(figsize=(8, 5), dpi=100)
        self.relative_sensitivity_ax = self.relative_sensitivity_figure.add_subplot(111)
        self.relative_sensitivity_canvas = FigureCanvasQTAgg(
            self.relative_sensitivity_figure
        )
        self.title = QLabel("Ranking and sensitivity analysis")
        self.sensitivity_scope = QLabel("Sensitivity intervals are valid only for the current dataset and active filters.")
        self.export_ranking_button = QPushButton("Export ranking PNG")
        self.export_ranking_button.clicked.connect(
            lambda: self.export_requested.emit("ranking")
        )
        self.export_sensitivity_button = QPushButton("Export sensitivity PNG")
        self.export_sensitivity_button.clicked.connect(
            lambda: self.export_requested.emit("sensitivity")
        )
        self.export_relative_sensitivity_button = QPushButton(
            "Export relative sensitivity PNG"
        )
        self.export_relative_sensitivity_button.clicked.connect(
            lambda: self.export_requested.emit("relative_sensitivity")
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)
        layout.addWidget(self.title)
        layout.addWidget(self.sensitivity_scope)

        chart_container = QWidget()
        chart_layout = QVBoxLayout(chart_container)
        chart_layout.setContentsMargins(0, 0, 0, 0)
        chart_layout.setSpacing(2)
        chart_layout.addWidget(self.ranking_canvas)
        chart_layout.addWidget(self.sensitivity_canvas)
        chart_layout.addWidget(self.relative_sensitivity_canvas)

        chart_scroll = QScrollArea()
        chart_scroll.setWidgetResizable(True)
        chart_scroll.setWidget(chart_container)

        export_buttons = QVBoxLayout()
        export_buttons.setContentsMargins(0, 0, 0, 0)
        export_buttons.setSpacing(6)
        export_buttons.addWidget(self.export_ranking_button)
        export_buttons.addWidget(self.export_sensitivity_button)
        export_buttons.addWidget(self.export_relative_sensitivity_button)
        export_buttons.addStretch()

        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)
        content_layout.addWidget(chart_scroll, 1)
        content_layout.addLayout(export_buttons)
        layout.addLayout(content_layout, 1)

    def update_chart(self, hta):
        self.ranking_ax.clear()
        self.sensitivity_ax.clear()
        self.relative_sensitivity_ax.clear()
        if hta.results is None or hta.results.get("ranking") is None:
            self.ranking_ax.text(0.5, 0.5, "No results", ha="center", va="center")
            self.sensitivity_ax.text(0.5, 0.5, "No results", ha="center", va="center")
            self.relative_sensitivity_ax.text(
                0.5, 0.5, "No results", ha="center", va="center"
            )
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
                self.sensitivity_ax.set_yticks(positions)
                self.sensitivity_ax.set_yticklabels(labels)
                self.sensitivity_ax.set_xlabel("Weight")
                self.sensitivity_ax.set_title(
                    f"Weight sensitivity\n{hta.dataset_label}; "
                    f"{len(hta.filtered_devices)} of {len(hta.devices)} devices"
                )
                self.sensitivity_ax.tick_params(axis="y", labelsize=8)
                self.relative_sensitivity_ax.set_xscale("symlog", linthresh=0.1)
                self.relative_sensitivity_ax.axvspan(
                    -0.1, 0.1, color="gray", alpha=0.08
                )
                self.relative_sensitivity_ax.axvline(
                    0, color="black", linewidth=1.5, label="Current weight"
                )
                for position, (_, values) in zip(positions, sensitivity.iterrows()):
                    self.relative_sensitivity_ax.hlines(
                        position,
                        float(values["delta_minus"]),
                        float(values["delta_plus"]),
                        color="#C0392B",
                        linewidth=10,
                        alpha=0.6,
                    )
                self.relative_sensitivity_ax.set_yticks(positions)
                self.relative_sensitivity_ax.set_yticklabels(labels)
                self.relative_sensitivity_ax.set_xticks(
                    [-1.0, -0.5, -0.2, -0.1, -0.05, 0, 0.05, 0.1, 0.2, 0.5, 1.0]
                )
                self.relative_sensitivity_ax.set_xticklabels(
                    ["-1.0", "-0.5", "-0.2", "-0.1", "-0.05", "0",
                     "0.05", "0.1", "0.2", "0.5", "1.0"]
                )
                self.relative_sensitivity_ax.set_xlim(-1.1, 1.1)
                self.relative_sensitivity_ax.set_xlabel("Relative weight change")
                self.relative_sensitivity_ax.set_title("Relative weight sensitivity")
                self.relative_sensitivity_ax.grid(
                    True, linestyle="--", alpha=0.4, axis="x"
                )
                self.relative_sensitivity_ax.legend(loc="upper right")
                self.relative_sensitivity_ax.tick_params(axis="y", labelsize=8)
            except Exception:
                self.sensitivity_ax.text(0.5, 0.5, "Sensitivity unavailable", ha="center", va="center")
                self.relative_sensitivity_ax.text(
                    0.5, 0.5, "Sensitivity unavailable", ha="center", va="center"
                )

        self.ranking_figure.tight_layout()
        self.sensitivity_figure.tight_layout()
        self.relative_sensitivity_figure.tight_layout()
        row_count = len(accepted) if hta.results is not None and "accepted" in locals() else 1
        row_count = max(row_count, len(sensitivity) if "sensitivity" in locals() else 1)
        chart_height = max(260, 22 * row_count + 90)
        for canvas in (
            self.ranking_canvas,
            self.sensitivity_canvas,
            self.relative_sensitivity_canvas,
        ):
            canvas.setMinimumHeight(chart_height)
        self.ranking_canvas.draw()
        self.sensitivity_canvas.draw()
        self.relative_sensitivity_canvas.draw()
