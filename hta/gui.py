from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QRadioButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QMessageBox,
    QListWidget,
    QCheckBox,
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from hta.analyzer import HTA


class HTAGUI(QMainWindow):
    """PySide6 shell for HTA analytics workflow."""

    def __init__(self):
        super().__init__()
        self.hta = HTA()
        self.filter_rules = []
        self.weight_fields = {}

        self.setWindowTitle("HTA Analytics")
        self.resize(1400, 900)

        self.method_group = QGroupBox("MCDA method")
        self.norm_group = QGroupBox("Normalization")
        self.source_group = QGroupBox("Data source")
        self.filter_group = QGroupBox("Filters")
        self.weights_group = QGroupBox("Weights")

        self.device_count_spin = QSpinBox()
        self.device_count_spin.setRange(2, 500)
        self.device_count_spin.setValue(20)

        self.data_table = QTableWidget()
        self.data_table.setAlternatingRowColors(True)
        self.results_table = QTableWidget()
        self.results_table.setAlternatingRowColors(True)

        self.filter_col_combo = QComboBox()
        self.filter_op_combo = QComboBox()
        self.filter_value_box = QDoubleSpinBox()
        self.filter_value_box.setRange(-1e9, 1e9)
        self.filter_value_box.setDecimals(6)
        self.filter_lower_box = QDoubleSpinBox()
        self.filter_lower_box.setRange(-1e9, 1e9)
        self.filter_lower_box.setDecimals(6)
        self.filter_upper_box = QDoubleSpinBox()
        self.filter_upper_box.setRange(-1e9, 1e9)
        self.filter_upper_box.setDecimals(6)
        self.filter_bool_check = QCheckBox("True")
        self.filter_list = QListWidget()

        self.figure = Figure(figsize=(5, 3), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.chart_title = QLabel("Ranking chart")

        self.setup_ui()
        self.refresh_filter_controls()
        self.refresh_weight_controls()
        self.refresh_preview_table()
        self.refresh_results_table()
        self.refresh_chart()

    def setup_ui(self):
        central = QWidget()
        root = QVBoxLayout(central)

        source_layout = QVBoxLayout(self.source_group)
        file_btn = QPushButton("Load data file")
        file_btn.clicked.connect(self.load_file_data)
        generate_btn = QPushButton("Generate demo data")
        generate_btn.clicked.connect(self.generate_demo_data)

        source_row = QHBoxLayout()
        source_row.addWidget(file_btn)
        source_row.addWidget(generate_btn)
        source_row.addWidget(QLabel("Device count:"))
        source_row.addWidget(self.device_count_spin)
        source_layout.addLayout(source_row)

        method_layout = QVBoxLayout(self.method_group)
        self.method_buttons = {}
        for method in ["SAW", "TOPSIS", "VIKOR"]:
            radio = QRadioButton(method)
            radio.setChecked(method == "SAW")
            self.method_buttons[method] = radio
            method_layout.addWidget(radio)

        norm_layout = QVBoxLayout(self.norm_group)
        self.norm_buttons = {}
        for method in ["minmax", "weitendorf", "z_score"]:
            radio = QRadioButton(method)
            radio.setChecked(method == "minmax")
            self.norm_buttons[method] = radio
            norm_layout.addWidget(radio)

        filter_form = QFormLayout()
        self.filter_op_combo.addItems(["eq", "neq", "gt", "gte", "lt", "lte", "between"])
        self.filter_col_combo.currentTextChanged.connect(self.on_filter_column_changed)
        self.filter_op_combo.currentTextChanged.connect(self.update_filter_controls_visibility)

        filter_form.addRow("Column:", self.filter_col_combo)
        filter_form.addRow("Operator:", self.filter_op_combo)
        filter_form.addRow("Value:", self.filter_value_box)
        filter_form.addRow("Lower:", self.filter_lower_box)
        filter_form.addRow("Upper:", self.filter_upper_box)
        filter_form.addRow("Bool value:", self.filter_bool_check)

        filter_buttons = QHBoxLayout()
        add_filter_btn = QPushButton("Add filter")
        add_filter_btn.clicked.connect(self.add_filter_rule)
        remove_filter_btn = QPushButton("Remove selected")
        remove_filter_btn.clicked.connect(self.remove_selected_filter)
        clear_filters_btn = QPushButton("Clear filters")
        clear_filters_btn.clicked.connect(self.clear_filters)
        apply_filters_btn = QPushButton("Apply filters")
        apply_filters_btn.clicked.connect(self.apply_filters_from_form)
        filter_buttons.addWidget(add_filter_btn)
        filter_buttons.addWidget(remove_filter_btn)
        filter_buttons.addWidget(clear_filters_btn)
        filter_buttons.addWidget(apply_filters_btn)

        filter_layout = QVBoxLayout(self.filter_group)
        filter_layout.addLayout(filter_form)
        filter_layout.addLayout(filter_buttons)
        filter_layout.addWidget(self.filter_list)

        weights_layout = QVBoxLayout(self.weights_group)
        self.weights_container = QWidget()
        self.weights_form = QFormLayout(self.weights_container)
        weights_layout.addWidget(self.weights_container)

        apply_weights_btn = QPushButton("Apply weights")
        apply_weights_btn.clicked.connect(self.apply_weights_from_form)
        weights_layout.addWidget(apply_weights_btn)

        action_layout = QHBoxLayout()
        run_btn = QPushButton("Run MCDA")
        run_btn.clicked.connect(self.run_analysis)
        export_csv_btn = QPushButton("Export CSV")
        export_csv_btn.clicked.connect(self.export_csv)
        export_xlsx_btn = QPushButton("Export XLSX")
        export_xlsx_btn.clicked.connect(self.export_xlsx)
        action_layout.addWidget(run_btn)
        action_layout.addWidget(export_csv_btn)
        action_layout.addWidget(export_xlsx_btn)

        table_layout = QHBoxLayout()
        data_panel = QWidget(); data_panel_layout = QVBoxLayout(data_panel)
        data_panel_layout.addWidget(QLabel("Data preview")); data_panel_layout.addWidget(self.data_table)

        results_panel = QWidget(); results_panel_layout = QVBoxLayout(results_panel)
        results_panel_layout.addWidget(QLabel("Results")); results_panel_layout.addWidget(self.results_table)

        table_layout.addWidget(data_panel, 2)
        table_layout.addWidget(results_panel, 1)

        root.addWidget(self.source_group)
        root.addWidget(self.method_group)
        root.addWidget(self.norm_group)
        root.addWidget(self.filter_group)
        root.addWidget(self.weights_group)
        root.addLayout(action_layout)
        root.addLayout(table_layout)
        root.addWidget(self.chart_title)
        root.addWidget(self.canvas)

        self.setCentralWidget(central)

    def update_filter_controls_visibility(self):
        operator = self.filter_op_combo.currentText()
        is_between = operator == "between"
        self.filter_value_box.setVisible(not is_between)
        self.filter_lower_box.setVisible(is_between)
        self.filter_upper_box.setVisible(is_between)
        self.filter_bool_check.setVisible(operator in {"eq", "neq"})

    def on_filter_column_changed(self):
        column = self.filter_col_combo.currentText()
        if not column or not self.hta.variables_config:
            return

        dtype = self.hta.variables_config.get(column, {}).get("dtype")
        if dtype == "bool":
            self.filter_op_combo.clear()
            self.filter_op_combo.addItems(["eq", "neq"])
        else:
            self.filter_op_combo.clear()
            self.filter_op_combo.addItems(["eq", "neq", "gt", "gte", "lt", "lte", "between"])

        self.update_filter_controls_visibility()

    def refresh_filter_controls(self):
        columns = list(self.hta.variables_config.keys()) if self.hta.variables_config else []
        self.filter_col_combo.clear()
        self.filter_col_combo.addItems(columns)
        if columns:
            self.filter_col_combo.setCurrentIndex(0)
        self.update_filter_controls_visibility()

    def refresh_weight_controls(self):
        while self.weights_form.count():
            item = self.weights_form.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.weight_fields = {}
        if not self.hta.variables_config:
            return

        for column, config in self.hta.variables_config.items():
            spin = QDoubleSpinBox()
            spin.setRange(0.0, 10.0)
            spin.setDecimals(3)
            spin.setSingleStep(0.1)
            current_weight = 1.0
            if self.hta.weights is not None and column in self.hta.weights:
                current_weight = float(self.hta.weights[column])
            spin.setValue(current_weight)
            self.weight_fields[column] = spin
            self.weights_form.addRow(f"{column}:", spin)

    def add_filter_rule(self):
        column = self.filter_col_combo.currentText()
        if not column:
            return

        operator = self.filter_op_combo.currentText()
        if operator in {"eq", "neq"}:
            dtype = self.hta.variables_config.get(column, {}).get("dtype")
            value = self.filter_bool_check.isChecked() if dtype == "bool" else self.filter_value_box.value()
            rule = {"column": column, "operator": operator, "value": value}
        elif operator == "between":
            rule = {"column": column, "operator": operator, "lower": self.filter_lower_box.value(), "upper": self.filter_upper_box.value()}
        else:
            rule = {"column": column, "operator": operator, "value": self.filter_value_box.value()}

        self.filter_rules.append(rule)
        if operator == "between":
            label = f"{column} {operator} [{rule['lower']}, {rule['upper']}]"
        else:
            label = f"{column} {operator} {rule['value']}"
        self.filter_list.addItem(label)

    def remove_selected_filter(self):
        current_row = self.filter_list.currentRow()
        if current_row < 0:
            return
        self.filter_rules.pop(current_row)
        self.filter_list.takeItem(current_row)

    def clear_filters(self):
        self.filter_rules = []
        self.filter_list.clear()

    def apply_filters_from_form(self):
        if not self.filter_rules:
            self.hta.filtered_devices = list(self.hta.devices)
            self.refresh_results_table()
            return

        self.hta.apply_filters(self.filter_rules)
        self.refresh_preview_table()
        self.refresh_results_table()

    def apply_weights_from_form(self):
        weights = {}
        for column, widget in self.weight_fields.items():
            weights[column] = widget.value()
        self.hta.set_weights(weights)
        self.refresh_results_table()
        self.refresh_chart()

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

    def refresh_preview_table(self):
        if self.hta.raw_data is None:
            self.data_table.setRowCount(0)
            self.data_table.setColumnCount(0)
            return

        df = self.hta.raw_data.copy()
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
            return

        df = self.hta.results["ranking"].copy()
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

    def refresh_chart(self):
        self.ax.clear()
        if self.hta.results is None or self.hta.results.get("ranking") is None:
            self.ax.text(0.5, 0.5, "No results", ha="center", va="center")
        else:
            ranking = self.hta.results["ranking"].copy()
            accepted = ranking[ranking["Status"] == "Accepted"].sort_values("Rank")
            if accepted.empty:
                self.ax.text(0.5, 0.5, "No accepted devices", ha="center", va="center")
            else:
                self.ax.barh(accepted.index, accepted["Score"].astype(float), color="#2E86DE")
                self.ax.invert_yaxis()
                self.ax.set_xlabel("Score")
                self.ax.set_title("Ranking")
        self.figure.tight_layout()
        self.canvas.draw()

    def load_file_data(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open HTA dataset", "", "CSV Files (*.csv);;Excel Files (*.xlsx *.xls)")
        if not path:
            return

        self.hta = HTA()
        self.hta.load_data(path)
        self.filter_rules = []
        self.filter_list.clear()
        self.refresh_filter_controls()
        self.refresh_weight_controls()
        self.refresh_preview_table()
        self.refresh_results_table()
        self.refresh_chart()

    def generate_demo_data(self):
        self.hta = HTA(n_devices=self.device_count_spin.value())
        self.filter_rules = []
        self.filter_list.clear()
        self.refresh_filter_controls()
        self.refresh_weight_controls()
        self.refresh_preview_table()
        self.refresh_results_table()
        self.refresh_chart()

    def run_analysis(self):
        if self.hta.raw_data is None:
            QMessageBox.warning(self, "No data", "Load data or generate demo data first.")
            return

        method = self._selected_method()
        norm = self._selected_norm()

        try:
            self.hta.run_mcda(method=method, norm_method=norm)
            self.refresh_results_table()
            self.refresh_chart()
        except Exception as exc:
            QMessageBox.critical(self, "Analysis error", str(exc))

    def export_csv(self):
        if self.hta.results is None or self.hta.results.get("ranking") is None:
            QMessageBox.warning(self, "No results", "Run analysis first.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Save ranking as CSV", "results.csv", "CSV Files (*.csv)")
        if path:
            self.hta.export_results(path)

    def export_xlsx(self):
        if self.hta.results is None or self.hta.results.get("ranking") is None:
            QMessageBox.warning(self, "No results", "Run analysis first.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Save ranking as XLSX", "results.xlsx", "Excel Files (*.xlsx)")
        if path:
            self.hta.export_results(path)


if __name__ == "__main__":
    app = QApplication([])
    window = HTAGUI()
    window.show()
    app.exec()
