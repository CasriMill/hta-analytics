from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class WeightsEditor(QWidget):
    status_changed = Signal(str)

    def __init__(self, hta):
        super().__init__()
        self.hta = hta
        self.weight_fields = {}
        self.group = QGroupBox("Weights")
        self.form = QFormLayout()
        self.container = QWidget()
        self.container.setLayout(self.form)

        layout = QVBoxLayout(self.group)
        layout.addWidget(self.container)
        apply_btn = QPushButton("Apply weights")
        apply_btn.clicked.connect(self.apply_weights)
        layout.addWidget(apply_btn)

    def set_hta(self, hta):
        self.hta = hta
        self.refresh_fields()

    def refresh_fields(self):
        for i in reversed(range(self.form.count())):
            item = self.form.takeAt(i)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.weight_fields = {}
        if not self.hta.variables_config:
            return

        for column in self.hta.variables_config:
            spin = QDoubleSpinBox()
            spin.setRange(0.0, 10.0)
            spin.setDecimals(3)
            spin.setSingleStep(0.1)
            current_weight = 1.0
            if self.hta.weights is not None and column in self.hta.weights:
                current_weight = float(self.hta.weights[column])
            spin.setValue(current_weight)
            self.weight_fields[column] = spin
            self.form.addRow(f"{column}:", spin)

    def apply_weights(self):
        weights = {column: widget.value() for column, widget in self.weight_fields.items()}
        self.hta.set_weights(weights)
        self.status_changed.emit("Weights applied")

    def widget(self):
        return self.group
