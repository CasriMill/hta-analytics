from __future__ import annotations

from PySide6.QtCore import Qt
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

        self.setWindowTitle("HTA Analytics")
        self.resize(1400, 900)
        self.setStatusBar(QStatusBar(self))
        self.statusBar().setStyleSheet("QStatusBar { border-top: 1px solid #d0d0d0; background: #f5f5f5; color: #222; }")
        self.statusBar().showMessage("Ready")

        self.method_group = QGroupBox("MCDA method")
        self.norm_group = QGroupBox("Normalization")
        self.action_group = QGroupBox("Actions")
        self.source_group = QGroupBox("Data source")

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
        self.filter_editor.status_changed.connect(self.set_status)
        self.weights_editor.status_changed.connect(self.set_status)

        self.setup_ui()
        self.refresh_filter_controls()
        self.refresh_weight_controls()
        self.refresh_preview_table()
        self.refresh_results_table()
        self.refresh_chart()

    def setup_ui(self):
        central = QWidget()
        root = QVBoxLayout(central)
        root.setSpacing(10)

        source_layout = QVBoxLayout(self.source_group)
        file_btn = QPushButton("Load data file")
        file_btn.clicked.connect(self.load_file_data)
        generate_btn = QPushButton("Generate demo data")
        generate_btn.clicked.connect(self.generate_demo_data)
        for button in (file_btn, generate_btn):
            button.setMinimumHeight(32)

        source_row = QHBoxLayout()
        source_row.setSpacing(8)
        source_row.addWidget(file_btn)
        source_row.addWidget(generate_btn)
        source_row.addWidget(QLabel("Device count:"))
        source_row.addWidget(self.device_count_spin)
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
        for method in ["minmax", "weitendorf", "z_score"]:
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
        for button in (run_btn, export_csv_btn, export_xlsx_btn):
            button.setMinimumHeight(34)
        action_layout.addWidget(run_btn)
        action_layout.addWidget(export_csv_btn)
        action_layout.addWidget(export_xlsx_btn)

        data_panel = QWidget(); data_panel_layout = QVBoxLayout(data_panel)
        data_panel_layout.addWidget(QLabel("Data preview")); data_panel_layout.addWidget(self.data_table)
        results_panel = QWidget(); results_panel_layout = QVBoxLayout(results_panel)
        results_panel_layout.addWidget(QLabel("Results")); results_panel_layout.addWidget(self.results_table)
        results_panel_layout.addWidget(QLabel("Raw data ordered by rank")); results_panel_layout.addWidget(self.ranked_data_table)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.weights_editor.widget(), "Weights")
        self.tabs.addTab(self.filter_editor.widget(), "Filters")
        self.tabs.addTab(data_panel, "rw_data")
        self.tabs.addTab(results_panel, "Results")
        self.tabs.addTab(self.chart_panel, "Graphs")

        analysis_controls = QWidget()
        analysis_layout = QHBoxLayout(analysis_controls)
        analysis_layout.setContentsMargins(0, 0, 0, 0)
        analysis_layout.setSpacing(10)
        analysis_layout.addWidget(self.method_group)
        analysis_layout.addWidget(self.norm_group)
        analysis_layout.addWidget(self.action_group, 1)

        root.addWidget(self.source_group)
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

    def load_file_data(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open HTA dataset", "", "CSV Files (*.csv);;Excel Files (*.xlsx *.xls)")
        if not path:
            return
        self.hta = HTA()
        self.hta.load_data(path)
        self.filter_editor.set_hta(self.hta)
        self.weights_editor.set_hta(self.hta)
        self.filter_editor.clear_filters()
        self.refresh_preview_table(); self.refresh_results_table(); self.refresh_chart()
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
        self.set_status(f"Generated demo dataset with {self.device_count_spin.value()} devices")

    def run_analysis(self):
        if self.hta.raw_data is None:
            QMessageBox.warning(self, "No data", "Load data or generate demo data first.")
            return
        method = self._selected_method(); norm = self._selected_norm()
        try:
            self.hta.run_mcda(method=method, norm_method=norm)
            self.refresh_results_table(); self.refresh_chart()
            self.set_status(f"Analysis complete: {method} / {norm} | {self._dataset_summary()}")
        except Exception as exc:
            QMessageBox.critical(self, "Analysis error", str(exc))
            self.set_status("Analysis failed")

    def export_csv(self):
        if self.hta.results is None or self.hta.results.get("ranking") is None:
            QMessageBox.warning(self, "No results", "Run analysis first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save ranking as CSV", "results.csv", "CSV Files (*.csv)")
        if path:
            self.hta.export_results(path)
            self.set_status(f"Exported CSV to {path}")

    def export_xlsx(self):
        if self.hta.results is None or self.hta.results.get("ranking") is None:
            QMessageBox.warning(self, "No results", "Run analysis first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save ranking as XLSX", "results.xlsx", "Excel Files (*.xlsx)")
        if path:
            self.hta.export_results(path)
            self.set_status(f"Exported XLSX to {path}")


if __name__ == "__main__":
    app = QApplication([])
    window = HTAGUI()
    window.show()
    app.exec()
