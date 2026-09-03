"""Left-hand form. Emits PersonData on every keystroke."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from signature_builder.core.models import PersonData
from signature_builder.core.sanitizer import compose_org_email

_FIELDS: tuple[tuple[str, str], ...] = (
    ("first_name", "Nombre"),
    ("last_name", "Apellido"),
    ("title", "Cargo"),
    ("department", "Departamento"),
    ("phone", "Teléfono"),
    ("website", "Web"),
    ("linkedin", "LinkedIn"),
)

_MODELS: tuple[tuple[str, str], ...] = ()

_SECTIONS = {
    "first_name": "INFORMACIÓN PERSONAL",
    "phone": "CONTACTO",
}


class FormPanel(QWidget):
    """Collects signature fields. Does not generate HTML."""

    data_changed = Signal(object)

    def __init__(self, email_domain: str = "cac.com.ar", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self._email_domain = email_domain
        self._inputs: dict[str, QLineEdit] = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 24, 24)
        layout.setSpacing(4)

        title = QLabel("Signature Builder")
        title.setObjectName("AppTitle")
        subtitle = QLabel("Firma corporativa CAC")
        subtitle.setObjectName("AppSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        self._template_group = QButtonGroup(self)
        self._templates: dict[QRadioButton, str] = {}

        form: QFormLayout | None = None
        for key, label in _FIELDS:
            if key in _SECTIONS:
                section = QLabel(_SECTIONS[key])
                section.setObjectName("SectionTitle")
                layout.addWidget(section)
                form = QFormLayout()
                form.setSpacing(8)
                layout.addLayout(form)
            if key == "website":
                self._add_email_row(form)
            field = QLineEdit()
            field.textChanged.connect(self._emit)
            self._inputs[key] = field
            caption = QLabel(label)
            caption.setObjectName("FieldLabel")
            if form is None:
                continue
            form.addRow(caption, field)
        layout.addStretch(1)

    def _add_email_row(self, form: QFormLayout | None) -> None:
        row = QWidget()
        inner = QHBoxLayout(row)
        inner.setContentsMargins(0, 0, 0, 0)
        inner.setSpacing(0)
        local = QLineEdit()
        local.setObjectName("EmailLocal")
        local.textChanged.connect(self._emit)
        self._inputs["email_local"] = local
        suffix = QLineEdit(f"@{self._email_domain}")
        suffix.setObjectName("EmailSuffix")
        suffix.setReadOnly(True)
        suffix.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        suffix.setFixedWidth(118)
        inner.addWidget(local, 1)
        inner.addWidget(suffix)
        caption = QLabel("Email")
        caption.setObjectName("FieldLabel")
        if form is not None:
            form.addRow(caption, row)

    def set_defaults(self, person: PersonData) -> None:
        """Fill the form without extra change noise beyond one emit at the end."""
        for key, field in self._inputs.items():
            field.blockSignals(True)
            if key == "email_local":
                local = person.email.split("@")[0] if person.email else ""
                field.setText(local)
            elif hasattr(person, key):
                field.setText(getattr(person, key))
            field.blockSignals(False)
        self._emit()

    def person(self) -> PersonData:
        """Return the current form values as PersonData."""
        return PersonData(
            first_name=self._inputs["first_name"].text(),
            last_name=self._inputs["last_name"].text(),
            title=self._inputs["title"].text(),
            department=self._inputs["department"].text(),
            phone=self._inputs["phone"].text(),
            email=compose_org_email(self._inputs["email_local"].text(), self._email_domain),
            website=self._inputs["website"].text(),
            linkedin=self._inputs["linkedin"].text(),
        )

    def template(self) -> str:
        """Return the signature model (always original)."""
        return "original"

    def _emit(self) -> None:
        self.data_changed.emit(self.person())
