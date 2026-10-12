from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
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
        self.value_box = QLineEdit()
        self.value_box.setPlaceholderText("Set value")
        self.lower_box = QLineEdit()
        self.lower_box.setPlaceholderText("Set lower value")
        self.upper_box = QLineEdit()
        self.upper_box.setPlaceholderText("Set upper value")
        self.choice_box = QComboBox()
        self.column_info = QLabel("Select a column")
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
        form.addRow("Data:", self.column_info)
        form.addRow("Operator:", self.op_combo)
        form.addRow("Value:", self.value_box)
        form.addRow("Lower:", self.lower_box)
        form.addRow("Upper:", self.upper_box)
        form.addRow("Choice:", self.choice_box)

        form_panel = QWidget()
        form_panel.setLayout(form)

        buttons = QVBoxLayout()
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
        buttons.addStretch()

        layout = QVBoxLayout(self.group)
        controls = QHBoxLayout()
        controls.addWidget(form_panel, 2)
        controls.addLayout(buttons, 1)
        layout.addLayout(controls)
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
            self.column_info.setText("Select a column")
            return
        dtype = self._column_dtype(column)
        if dtype == "bool":
            self.op_combo.clear()
            self.op_combo.addItems(["eq", "neq"])
            self._set_choice_values(column, [True, False])
            self.column_info.setText("bool | True / False")
        elif dtype == "int":
            self.op_combo.clear()
            self.op_combo.addItems(["eq", "neq", "gt", "gte", "lt", "lte", "between"])
            self._set_choice_values(column)
            self._set_numeric_values(column, dtype)
        elif dtype == "float":
            self.op_combo.clear()
            self.op_combo.addItems(["eq", "neq", "gt", "gte", "lt", "lte", "between"])
            self.choice_box.clear()
            self._set_numeric_values(column, dtype)
        else:
            self.op_combo.clear()
            self.op_combo.addItems(["eq", "neq"])
            self._set_choice_values(column)
            self.column_info.setText(f"category | {self.choice_box.count()} unique values")
        self.update_visibility()

    def _column_dtype(self, column):
        configured_dtype = self.hta.variables_config.get(column, {}).get("dtype")
        if configured_dtype:
            return configured_dtype
        if self.hta.raw_data is not None and column in self.hta.raw_data:
            return str(self.hta.raw_data[column].dtype)
        return "float"

    def _set_numeric_values(self, column, dtype):
        if self.hta.raw_data is None or column not in self.hta.raw_data:
            self.column_info.setText(f"{dtype}")
            return

        series = self.hta.raw_data[column].dropna()
        if series.empty:
            self.column_info.setText(f"{dtype} | no values")
            return

        minimum = float(series.min())
        mean = float(series.mean())
        median = float(series.median())
        maximum = float(series.max())
        self.column_info.setText(
            f"{dtype} | min {minimum:g} | mean {mean:g} | median {median:g} | max {maximum:g}"
        )
        self.value_box.setText(f"{median:g}")
        self.lower_box.setText(f"{minimum:g}")
        self.upper_box.setText(f"{maximum:g}")

    def _set_choice_values(self, column, values=None):
        self.choice_box.clear()
        if values is None and self.hta.raw_data is not None and column in self.hta.raw_data:
            values = sorted(self.hta.raw_data[column].dropna().unique().tolist(), key=str)
        for value in values or []:
            self.choice_box.addItem(str(value), userData=value)

    def _numeric_value(self, field):
        try:
            return float(field.text())
        except ValueError as exc:
            raise ValueError("Filter value must be numeric.") from exc

    def update_visibility(self):
        column = self.col_combo.currentText()
        operator = self.op_combo.currentText()
        is_between = operator == "between"
        dtype = self._column_dtype(column) if column else ""
        is_choice = dtype in {"bool", "category", "str", "object"}
        is_choice = is_choice or (dtype == "int" and operator in {"eq", "neq"})
        self.value_box.setVisible(not is_between and not is_choice)
        self.lower_box.setVisible(is_between)
        self.upper_box.setVisible(is_between)
        self.choice_box.setVisible(not is_between and is_choice)

    def _is_numeric_column(self, column):
        return self._column_dtype(column) in {"int", "float"}

    def add_filter_rule(self):
        column = self.col_combo.currentText()
        if not column:
            return
        operator = self.op_combo.currentText()
        if operator in {"eq", "neq"}:
            dtype = self._column_dtype(column)
            if dtype in {"bool", "int"} or dtype not in {"float"}:
                value = self.choice_box.currentData()
            else:
                value = self._numeric_value(self.value_box)
            rule = {"column": column, "operator": operator, "value": value}
        elif operator == "between":
            rule = {"column": column, "operator": operator, "lower": self._numeric_value(self.lower_box), "upper": self._numeric_value(self.upper_box)}
        else:
            rule = {"column": column, "operator": operator, "value": self._numeric_value(self.value_box)}

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
