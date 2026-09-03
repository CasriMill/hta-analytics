from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class FilterEditor(QWidget):
    status_changed = Signal(str)

    def __init__(self, hta):
        super().__init__()
        self.hta = hta
        self.filter_rules = []

        self.group = QGroupBox("Filters")
        self.col_combo = QComboBox()
        self.op_combo = QComboBox()
        self.value_box = QDoubleSpinBox()
        self.value_box.setRange(-1e9, 1e9)
        self.value_box.setDecimals(6)
        self.lower_box = QDoubleSpinBox()
        self.lower_box.setRange(-1e9, 1e9)
        self.lower_box.setDecimals(6)
        self.upper_box = QDoubleSpinBox()
        self.upper_box.setRange(-1e9, 1e9)
        self.upper_box.setDecimals(6)
        self.bool_check = QCheckBox("True")
        self.list_widget = QListWidget()
        self.status_label = QLabel("Not applied")

        self._setup_ui()
        self.refresh_controls()

    def _setup_ui(self):
        form = QFormLayout()
        self.op_combo.addItems(["eq", "neq", "gt", "gte", "lt", "lte", "between"])
        self.col_combo.currentTextChanged.connect(self.on_column_changed)
        self.op_combo.currentTextChanged.connect(self.update_visibility)

        form.addRow("Column:", self.col_combo)
        form.addRow("Operator:", self.op_combo)
        form.addRow("Value:", self.value_box)
        form.addRow("Lower:", self.lower_box)
        form.addRow("Upper:", self.upper_box)
        form.addRow("Bool value:", self.bool_check)

        buttons = QHBoxLayout()
        add_btn = QPushButton("Add filter")
        add_btn.clicked.connect(self.add_filter_rule)
        remove_btn = QPushButton("Remove selected")
        remove_btn.clicked.connect(self.remove_selected_filter)
        clear_btn = QPushButton("Clear filters")
        clear_btn.clicked.connect(self.clear_filters)
        apply_btn = QPushButton("Apply filters")
        apply_btn.clicked.connect(self.apply_filters)

        buttons.addWidget(add_btn)
        buttons.addWidget(remove_btn)
        buttons.addWidget(clear_btn)
        buttons.addWidget(apply_btn)

        layout = QVBoxLayout(self.group)
        layout.addLayout(form)
        layout.addLayout(buttons)
        layout.addWidget(self.status_label)
        layout.addWidget(self.list_widget)

    def set_hta(self, hta):
        self.hta = hta
        self.refresh_controls()

    def refresh_controls(self):
        columns = list(self.hta.variables_config.keys()) if self.hta.variables_config else []
        self.col_combo.clear()
        self.col_combo.addItems(columns)
        if columns:
            self.col_combo.setCurrentIndex(0)
        self.on_column_changed()
        self.update_visibility()

    def on_column_changed(self):
        column = self.col_combo.currentText()
        if not column or not self.hta.variables_config:
            return
        dtype = self.hta.variables_config.get(column, {}).get("dtype")
        if dtype == "bool":
            self.op_combo.clear()
            self.op_combo.addItems(["eq", "neq"])
        else:
            self.op_combo.clear()
            self.op_combo.addItems(["eq", "neq", "gt", "gte", "lt", "lte", "between"])
        self.update_visibility()

    def update_visibility(self):
        operator = self.op_combo.currentText()
        is_between = operator == "between"
        self.value_box.setVisible(not is_between)
        self.lower_box.setVisible(is_between)
        self.upper_box.setVisible(is_between)
        self.bool_check.setVisible(operator in {"eq", "neq"})

    def add_filter_rule(self):
        column = self.col_combo.currentText()
        if not column:
            return
        operator = self.op_combo.currentText()
        if operator in {"eq", "neq"}:
            dtype = self.hta.variables_config.get(column, {}).get("dtype")
            value = self.bool_check.isChecked() if dtype == "bool" else self.value_box.value()
            rule = {"column": column, "operator": operator, "value": value}
        elif operator == "between":
            rule = {"column": column, "operator": operator, "lower": self.lower_box.value(), "upper": self.upper_box.value()}
        else:
            rule = {"column": column, "operator": operator, "value": self.value_box.value()}

        self.filter_rules.append(rule)
        if operator == "between":
            label = f"{column} {operator} [{rule['lower']}, {rule['upper']}]"
        else:
            label = f"{column} {operator} {rule['value']}"
        self.list_widget.addItem(label)

    def remove_selected_filter(self):
        current_row = self.list_widget.currentRow()
        if current_row < 0:
            return
        self.filter_rules.pop(current_row)
        self.list_widget.takeItem(current_row)

    def clear_filters(self):
        self.filter_rules = []
        self.list_widget.clear()
        self.status_label.setText("Not applied")
        self.status_changed.emit("Filters cleared; click Apply filters")

    def apply_filters(self):
        if not self.filter_rules:
            self.hta.filtered_devices = list(self.hta.devices)
        else:
            self.hta.apply_filters(self.filter_rules)
        count = len(self.hta.filtered_devices)
        self.status_label.setText(f"Applied: {count} devices")
        self.status_changed.emit(f"Filters applied: {count} devices")

    def widget(self):
        return self.group
