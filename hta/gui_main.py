from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QRadioButton,
    QStatusBar,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QMessageBox,
    QPlainTextEdit,
)

from hta.analyzer import HTA
from hta.chart_panel import ChartPanel
from hta.filter_editor import FilterEditor
from hta.weights_editor import WeightsEditor


class HTAGUI(QMainWindow):
    """PySide6 shell for HTA analytics workflow."""

    def __init__(self):
        super().__init__()
        self.hta = HTA()

        self.setWindowTitle("HTA Analytics 0.4.0")
        self.resize(1400, 900)
        self.setStatusBar(QStatusBar(self))
        self.statusBar().setStyleSheet("QStatusBar { border-top: 1px solid #d0d0d0; background: #f5f5f5; color: #222; }")
        self.statusBar().showMessage("Ready")

        self.method_group = QGroupBox("MCDA method")
        self.norm_group = QGroupBox("Normalization")
        self.action_group = QGroupBox("Actions")
        self.source_group = QGroupBox("Data source")
        self.import_protocol = QPlainTextEdit()
        self.import_protocol.setReadOnly(True)
        self.import_protocol.setMinimumHeight(130)

        self.device_count_spin = QSpinBox()
        self.device_count_spin.setRange(2, 500)
        self.device_count_spin.setValue(20)

        self.data_table = QTableWidget()
        self.data_table.setAlternatingRowColors(True)
        self.results_table = QTableWidget()
        self.results_table.setAlternatingRowColors(True)
        self.ranked_data_table = QTableWidget()
        self.ranked_data_table.setAlternatingRowColors(True)

        self.filter_editor = FilterEditor(self.hta)
        self.weights_editor = WeightsEditor(self.hta)
        self.chart_panel = ChartPanel()
        self.chart_panel.export_requested.connect(self.export_chart_png)
        self.filter_editor.status_changed.connect(self.set_status)
        self.weights_editor.status_changed.connect(self.set_status)

        self.setup_ui()
        self.refresh_filter_controls()
        self.refresh_weight_controls()
        self.refresh_preview_table()
        self.refresh_results_table()
        self.refresh_chart()
        self.refresh_import_protocol("No source", "Ready")

    def setup_ui(self):
        central = QWidget()
        root = QVBoxLayout(central)
        root.setSpacing(10)

        source_layout = QVBoxLayout(self.source_group)
        file_btn = QPushButton("Load data file")
        file_btn.clicked.connect(self.load_file_data)
        generate_btn = QPushButton("Generate demo data")
        generate_btn.clicked.connect(self.generate_demo_data)
        help_btn = QPushButton("Help / Workflow")
        help_btn.clicked.connect(self.open_help)
        for button in (file_btn, generate_btn):
            button.setMinimumHeight(32)

        source_row = QHBoxLayout()
        source_row.setSpacing(8)
        source_row.addWidget(file_btn)
        source_row.addWidget(generate_btn)
        source_row.addWidget(QLabel("Device count:"))
        source_row.addWidget(self.device_count_spin)
        source_row.addWidget(help_btn)
        source_layout.addLayout(source_row)

        method_layout = QVBoxLayout(self.method_group)
        method_layout.setContentsMargins(8, 6, 8, 6)
        method_layout.setSpacing(4)
        self.method_buttons = {}
        for method in ["SAW", "TOPSIS", "VIKOR"]:
            radio = QRadioButton(method)
            radio.setChecked(method == "SAW")
            self.method_buttons[method] = radio
            method_layout.addWidget(radio)

        norm_layout = QVBoxLayout(self.norm_group)
        norm_layout.setContentsMargins(8, 6, 8, 6)
        norm_layout.setSpacing(4)
        self.norm_buttons = {}
        for method in [
            "minmax", "weitendorf", "z_score", "max", "juttler_korth",
            "sum", "vector", "sigmoid", "peldchus_t2", "peldchus_t3",
        ]:
            radio = QRadioButton(method)
            radio.setChecked(method == "minmax")
            self.norm_buttons[method] = radio
            norm_layout.addWidget(radio)

        action_layout = QVBoxLayout(self.action_group)
        action_layout.setContentsMargins(8, 6, 8, 6)
        action_layout.setSpacing(8)
        run_btn = QPushButton("Run MCDA")
        run_btn.clicked.connect(self.run_analysis)
        export_csv_btn = QPushButton("Export CSV")
        export_csv_btn.clicked.connect(self.export_csv)
        export_xlsx_btn = QPushButton("Export XLSX")
        export_xlsx_btn.clicked.connect(self.export_xlsx)
        run_btn.setMinimumHeight(34)
        action_layout.addWidget(run_btn)

        import_panel = QWidget()
        import_panel_layout = QVBoxLayout(import_panel)
        import_panel_layout.addWidget(self.source_group)
        import_content_layout = QHBoxLayout()
        import_table_layout = QVBoxLayout()
        import_table_layout.addWidget(QLabel("Raw data preview"))
        import_table_layout.addWidget(self.data_table)
        import_protocol_layout = QVBoxLayout()
        import_protocol_layout.addWidget(QLabel("Import protocol"))
        import_protocol_layout.addWidget(self.import_protocol)
        import_content_layout.addLayout(import_table_layout, 3)
        import_content_layout.addLayout(import_protocol_layout, 1)
        import_panel_layout.addLayout(import_content_layout)
        results_panel = QWidget(); results_panel_layout = QVBoxLayout(results_panel)
        results_content_layout = QHBoxLayout()
        results_tables_layout = QVBoxLayout()
        export_csv_btn = QPushButton("Export CSV")
        export_csv_btn.clicked.connect(self.export_csv)
        export_xlsx_btn = QPushButton("Export XLSX")
        export_xlsx_btn.clicked.connect(self.export_xlsx)
        results_tables_layout.addWidget(QLabel("Results"))
        results_tables_layout.addWidget(self.results_table)
        results_tables_layout.addWidget(QLabel("Raw data ordered by rank"))
        results_tables_layout.addWidget(self.ranked_data_table)
        results_export_layout = QVBoxLayout()
        results_export_layout.setSpacing(6)
        results_export_layout.addWidget(export_csv_btn)
        results_export_layout.addWidget(export_xlsx_btn)
        results_export_layout.addStretch()
        results_content_layout.addLayout(results_tables_layout, 1)
        results_content_layout.addLayout(results_export_layout)
        results_panel_layout.addLayout(results_content_layout)

        self.tabs = QTabWidget()
        self.tabs.addTab(import_panel, "Import")
        self.tabs.addTab(self.weights_editor.widget(), "Weights")
        self.tabs.addTab(self.filter_editor.widget(), "Filters")
        self.tabs.addTab(results_panel, "Results")
        self.tabs.addTab(self.chart_panel, "Graphs")

        analysis_controls = QWidget()
        analysis_layout = QHBoxLayout(analysis_controls)
        analysis_layout.setContentsMargins(0, 0, 0, 0)
        analysis_layout.setSpacing(10)
        analysis_layout.addWidget(self.method_group)
        analysis_layout.addWidget(self.norm_group)
        analysis_layout.addWidget(self.action_group, 1)

        root.addWidget(analysis_controls)
        root.addWidget(self.tabs)

        self.setCentralWidget(central)

    def refresh_filter_controls(self):
        self.filter_editor.set_hta(self.hta)

    def refresh_weight_controls(self):
        self.weights_editor.set_hta(self.hta)

    def refresh_preview_table(self):
        if self.hta.raw_data is None:
            self.data_table.setRowCount(0)
            self.data_table.setColumnCount(0)
            return

        df = self.hta.raw_data.copy()
        df.insert(0, "Device_ID", df.index)
        rows, cols = df.shape
        self.data_table.setRowCount(rows)
        self.data_table.setColumnCount(cols)
        self.data_table.setHorizontalHeaderLabels(list(df.columns))

        for row_index in range(rows):
            for col_index in range(cols):
                value = df.iloc[row_index, col_index]
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.data_table.setItem(row_index, col_index, item)

    def refresh_import_protocol(self, source, status="Ready"):
        if self.hta.raw_data is None:
                self.import_protocol.setPlainText(f"Status: {status}\nNo dataset loaded.")
                return
        numeric = sum(
                config.get("dtype") in {"int", "float", "bool"}
                for config in self.hta.variables_config.values()
        )
        categorical = len(self.hta.variables_config) - numeric
        lines = [
                f"Status: {status}",
                f"Source: {source}",
                f"Devices: {len(self.hta.devices)}",
                f"Criteria: {len(self.hta.variables_config)}",
                f"Numeric/bool MCDA candidates: {numeric}",
                f"Categorical/filter-only criteria: {categorical}",
                f"Imported weights: {'yes' if self.hta.weights is not None else 'no'}",
        ]
        if getattr(self.hta, "imported_weight_adjustments", {}):
                lines.append("Warnings:")
                for column, value in self.hta.imported_weight_adjustments.items():
                    lines.append(f"- Negative weight adjusted to zero: {column} ({value:g})")
        if getattr(self.hta, "import_validation_issues", []):
                lines.append("Validation warnings:")
                lines.extend(f"- {issue}" for issue in self.hta.import_validation_issues)
        if getattr(self.hta, "import_dropped_devices", []):
                lines.append(
                    "Excluded device rows: "
                    + ", ".join(map(str, self.hta.import_dropped_devices))
                )
        self.import_protocol.setPlainText("\n".join(lines))

    def refresh_results_table(self):
        if self.hta.results is None or self.hta.results.get("ranking") is None:
            self.results_table.setRowCount(0)
            self.results_table.setColumnCount(0)
            self.ranked_data_table.setRowCount(0)
            self.ranked_data_table.setColumnCount(0)
            return

        df = self.hta.results["ranking"].copy()
        df.insert(0, "Device_ID", df.index)
        rows, cols = df.shape
        self.results_table.setRowCount(rows)
        self.results_table.setColumnCount(cols)
        self.results_table.setHorizontalHeaderLabels(list(df.columns))

        for row_index in range(rows):
            for col_index in range(cols):
                value = df.iloc[row_index, col_index]
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.results_table.setItem(row_index, col_index, item)

        if self.hta.raw_data is None:
            return
        ordered = self.hta.raw_data.reindex(df.index).copy()
        ordered.insert(0, "Device_ID", ordered.index)
        ordered.insert(1, "Rank", df["Rank"].to_numpy())
        rows, cols = ordered.shape
        self.ranked_data_table.setRowCount(rows)
        self.ranked_data_table.setColumnCount(cols)
        self.ranked_data_table.setHorizontalHeaderLabels(list(ordered.columns))
        for row_index in range(rows):
            for col_index in range(cols):
                value = ordered.iloc[row_index, col_index]
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.ranked_data_table.setItem(row_index, col_index, item)

    def refresh_chart(self):
        self.chart_panel.update_chart(self.hta)

    def set_status(self, message: str):
        self.statusBar().showMessage(message, 4000)

    def _dataset_summary(self):
        if self.hta.raw_data is None:
            return "No dataset loaded"
        return f"Dataset: {self.hta.raw_data.shape[0]} rows × {self.hta.raw_data.shape[1]} columns"

    def _selected_method(self):
        for name, radio in self.method_buttons.items():
            if radio.isChecked():
                return name
        return "SAW"

    def _selected_norm(self):
        for name, radio in self.norm_buttons.items():
            if radio.isChecked():
                return name
        return "minmax"

    def open_help(self):
        readme_path = Path(__file__).resolve().parent.parent / "README.md"
        if not readme_path.exists():
            QMessageBox.warning(self, "Help unavailable", "README.md was not found.")
            return
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(readme_path))):
            QMessageBox.warning(
                self,
                "Help unavailable",
                f"Could not open the workflow help:\n{readme_path}",
            )

    def load_file_data(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open HTA dataset", "", "CSV Files (*.csv);;Excel Files (*.xlsx *.xls)")
        if not path:
            return
        self.hta = HTA()
        if not self.hta.load_data(path):
            QMessageBox.critical(self, "Import error", f"Could not import dataset:\n{path}")
            return
        self.filter_editor.set_hta(self.hta)
        self.weights_editor.set_hta(self.hta)
        self.filter_editor.clear_filters()
        self.refresh_preview_table(); self.refresh_results_table(); self.refresh_chart()
        self.refresh_import_protocol(path, "Imported")
        if self.hta.imported_weight_adjustments:
            adjustments = "\n".join(
                f"- {column}: {value:g} -> 0"
                for column, value in self.hta.imported_weight_adjustments.items()
            )
            answer = QMessageBox.question(
                self,
                "Negative imported weights",
                "Negative imported weights are invalid and will be set to zero:\n\n"
                f"{adjustments}\n\nContinue with the adjusted values?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer == QMessageBox.No:
                self.hta = HTA()
                self.filter_editor.set_hta(self.hta)
                self.weights_editor.set_hta(self.hta)
                self.refresh_preview_table()
                self.refresh_import_protocol("No source", "Import cancelled")
                return
        if self.hta.import_validation_issues:
            answer = QMessageBox.question(
                self,
                "Import validation warnings",
                "Invalid imported values were found. Affected device rows will "
                "be excluded from MCDA.\n\n"
                + "\n".join(f"- {issue}" for issue in self.hta.import_validation_issues)
                + "\n\nContinue with the proposed repairs?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer == QMessageBox.No:
                self.hta = HTA()
                self.filter_editor.set_hta(self.hta)
                self.weights_editor.set_hta(self.hta)
                self.refresh_preview_table()
                self.refresh_import_protocol("No source", "Import cancelled")
                return
        if self.hta.weights is not None:
            self.set_status(f"Loaded dataset and activated imported weights from {path}")
        else:
            self.set_status(f"Loaded dataset from {path}; weights require configuration")

    def generate_demo_data(self):
        self.hta = HTA(n_devices=self.device_count_spin.value())
        self.filter_editor.set_hta(self.hta)
        self.weights_editor.set_hta(self.hta)
        self.filter_editor.clear_filters()
        self.refresh_preview_table(); self.refresh_results_table(); self.refresh_chart()
        self.refresh_import_protocol("Generated demo data", "Generated")
        self.set_status(f"Generated demo dataset with {self.device_count_spin.value()} devices")

    def run_analysis(self):
        if self.hta.raw_data is None:
            QMessageBox.warning(self, "No data", "Load data or generate demo data first.")
            return
        method = self._selected_method(); norm = self._selected_norm()
        if not self._confirm_mcda_exclusions():
            self.tabs.setCurrentIndex(0)
            return
        try:
            self.hta.run_mcda(method=method, norm_method=norm)
            self.refresh_results_table(); self.refresh_chart()
            self.set_status(f"Analysis complete: {method} / {norm} | {self._dataset_summary()}")
        except Exception as exc:
            QMessageBox.critical(self, "Analysis error", str(exc))
            self.set_status("Analysis failed")

    def _confirm_mcda_exclusions(self):
        if not self.weights_editor.weights_changed_manually:
            return True

        exclusions = {}
        if self.hta.weights is not None:
            for column, weight in self.hta.weights.items():
                if float(weight) <= 1e-12:
                    exclusions[column] = "zero weight"
        for column, config in self.hta.variables_config.items():
            if config.get("dtype") not in {"int", "float", "bool"}:
                exclusions[column] = "categorical/filter-only criterion"
                continue
            if self.hta.raw_data is not None and self.hta.filtered_devices:
                values = self.hta.raw_data.loc[self.hta.filtered_devices, column]
                if values.nunique(dropna=True) <= 1:
                    exclusions[column] = "no variation after filtering"

        if not exclusions:
            return True

        details = "\n".join(
            f"- {column}: {reason}"
            for column, reason in exclusions.items()
        )
        answer = QMessageBox.question(
            self,
            "Criteria excluded from MCDA",
            "The following criteria will not participate in MCDA. "
            "The reason is shown after each item:\n\n"
            f"{details}\n\nContinue with these criteria excluded?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return answer == QMessageBox.Yes

    def export_csv(self):
        if self.hta.results is None or self.hta.results.get("ranking") is None:
            QMessageBox.warning(self, "No results", "Run analysis first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save ranking as CSV", "results.csv", "CSV Files (*.csv)")
        if path and self._confirm_overwrite(path):
            self.hta.export_results(path)
            self.statusBar().showMessage(f"Results exported to {path}", 4000)
            self.set_status(f"Exported CSV to {path}")

    def export_xlsx(self):
        if self.hta.results is None or self.hta.results.get("ranking") is None:
            QMessageBox.warning(self, "No results", "Run analysis first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save ranking as XLSX", "results.xlsx", "Excel Files (*.xlsx)")
        if path and self._confirm_overwrite(path):
            self.hta.export_results(path)
            self.statusBar().showMessage(f"Results exported to {path}", 4000)

    def _confirm_overwrite(self, path):
        if not os.path.exists(path):
            return True
        answer = QMessageBox.question(
            self,
            "File already exists",
            f"The file already exists:\n{path}\n\nOverwrite it?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return answer == QMessageBox.Yes

    def export_chart_png(self, chart_name):
        if chart_name == "ranking":
            figure = self.chart_panel.ranking_figure
            title = "Save ranking chart as PNG"
            default_name = "ranking.png"
        elif chart_name == "sensitivity":
            figure = self.chart_panel.sensitivity_figure
            title = "Save sensitivity chart as PNG"
            default_name = "sensitivity.png"
        elif chart_name == "relative_sensitivity":
            figure = self.chart_panel.relative_sensitivity_figure
            title = "Save relative sensitivity chart as PNG"
            default_name = "relative_sensitivity.png"
        else:
            raise ValueError(f"Unknown chart name: {chart_name}")

        path, _ = QFileDialog.getSaveFileName(
            self,
            title,
            default_name,
            "PNG Files (*.png)",
        )
        if path and self._confirm_overwrite(path):
            figure.savefig(path, dpi=600, format="png", bbox_inches="tight")
            self.statusBar().showMessage(f"Chart exported to {path}", 4000)
            self.set_status(f"Exported {chart_name} chart to {path}")


if __name__ == "__main__":
    app = QApplication([])
    window = HTAGUI()
    window.show()
    app.exec()
