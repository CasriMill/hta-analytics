from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QHBoxLayout,
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
        self.status_label = QLabel("Weights are not applied")
        self.check_btn = QPushButton("Check weight sum")
        self.recalculate_btn = QPushButton("Recalculate to 1.0")
        self.apply_btn = QPushButton("Apply weights")
        self.recalculate_btn.setVisible(False)
        self.apply_btn.setEnabled(False)

        layout = QVBoxLayout(self.group)
        layout.addWidget(self.container)
        layout.addWidget(self.status_label)
        buttons = QHBoxLayout()
        self.check_btn.clicked.connect(self.check_weights)
        self.recalculate_btn.clicked.connect(self.recalculate_weights)
        self.apply_btn.clicked.connect(self.apply_weights)
        buttons.addWidget(self.check_btn)
        buttons.addWidget(self.recalculate_btn)
        buttons.addWidget(self.apply_btn)
        layout.addLayout(buttons)

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
            self._set_applied_state(False)
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
            spin.valueChanged.connect(self._weights_changed)
            self.weight_fields[column] = spin
            self.form.addRow(f"{column}:", spin)

        self._set_applied_state(self.hta.weights is not None)

    def _set_applied_state(self, applied):
        if applied:
            self.status_label.setText("Weights are applied")
            self.apply_btn.setText("Weights are applied")
            self.apply_btn.setEnabled(False)
            self.check_btn.setEnabled(True)
            self.recalculate_btn.setVisible(False)
        else:
            self.status_label.setText("Weights changed; check the sum")
            self.apply_btn.setText("Apply weights")
            self.apply_btn.setEnabled(False)

    def _weights_changed(self):
        self.status_label.setText("Weights changed; check the sum")
        self.apply_btn.setText("Apply weights")
        self.apply_btn.setEnabled(False)
        self.recalculate_btn.setVisible(False)

    def _current_weights(self):
        return {column: widget.value() for column, widget in self.weight_fields.items()}

    def check_weights(self):
        total = sum(self._current_weights().values())
        if total <= 0:
            self.status_label.setText("Invalid sum: weights must be greater than 0")
            self.recalculate_btn.setVisible(False)
            self.apply_btn.setEnabled(False)
            return False

        if abs(total - 1.0) > 1e-6:
            self.status_label.setText(f"Sum is {total:.6f}; recalculation required")
            self.recalculate_btn.setVisible(True)
            self.apply_btn.setEnabled(False)
            return False

        self.status_label.setText("Sum is 1.000000; weights are ready to apply")
        self.recalculate_btn.setVisible(False)
        self.apply_btn.setEnabled(True)
        return True

    def recalculate_weights(self):
        weights = self._current_weights()
        total = sum(weights.values())
        if total <= 0:
            self.check_weights()
            return
        for column, value in weights.items():
            self.weight_fields[column].setValue(value / total)
        self.check_weights()

    def apply_weights(self):
        if not self.check_weights():
            return
        weights = self._current_weights()
        self.hta.set_weights(weights)
        self._set_applied_state(True)
        self.status_changed.emit("Weights applied")

    def widget(self):
        return self.group
