"""Nowoczesny wygląd interfejsu (Qt Style Sheets)."""

AKCENT = "#2fb35f"
AKCENT_CIEMNY = "#0d5f31"


def _paleta(dark: bool) -> dict:
    if dark:
        return {
            "bg": "#1b1f22", "panel": "#252b2f", "panel2": "#2d3438",
            "text": "#e8edf0", "muted": "#9aa7ad", "border": "#394247",
            "hover": "#33413a", "table": "#202528", "table_alt": "#262d31",
            "input": "#1f2528", "danger": "#ef5b46", "danger_dark": "#c33f2d",
        }
    return {
        "bg": "#f3f6f4", "panel": "#ffffff", "panel2": "#eef3ef",
        "text": "#1c2520", "muted": "#66736b", "border": "#d8e2da",
        "hover": "#e2f3e7", "table": "#ffffff", "table_alt": "#f5f9f6",
        "input": "#ffffff", "danger": "#d9482f", "danger_dark": "#b5361f",
    }


def stylesheet(motyw: str) -> str:
    dark = motyw == "dark"
    p = _paleta(dark)
    return f"""
    QWidget {{
        background: {p['bg']};
        color: {p['text']};
        font-family: "Segoe UI", "Noto Sans", "Inter", sans-serif;
        font-size: 14px;
    }}
    QMainWindow {{ background: {p['bg']}; }}
    QFrame#card, QGroupBox {{
        background: {p['panel']};
        border: 1px solid {p['border']};
        border-radius: 14px;
        padding: 14px;
    }}
    QGroupBox {{
        font-weight: 600;
        margin-top: 18px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 14px;
        padding: 0 6px;
        color: {p['muted']};
    }}
    QLabel#title {{ font-size: 26px; font-weight: 700; }}
    QLabel#subtitle {{ color: {p['muted']}; font-size: 14px; }}
    QLabel#hint {{ color: {p['muted']}; }}
    QLabel#link {{ color: {AKCENT}; text-decoration: underline; }}

    QListWidget#nav {{
        background: transparent;
        border: none;
        padding: 8px;
    }}
    QListWidget#nav::item {{
        height: 46px;
        padding-left: 14px;
        border-radius: 10px;
        color: {p['text']};
    }}
    QListWidget#nav::item:hover {{ background: {p['hover']}; }}
    QListWidget#nav::item:selected {{
        background: {AKCENT};
        color: #ffffff;
        font-weight: 600;
    }}

    QLineEdit, QComboBox, QSpinBox {{
        background: {p['input']};
        border: 1px solid {p['border']};
        border-radius: 10px;
        padding: 9px 12px;
        selection-background-color: {AKCENT};
    }}
    QLineEdit:focus, QComboBox:focus {{ border: 2px solid {AKCENT}; }}

    QPushButton {{
        background: {p['panel2']};
        border: 1px solid {p['border']};
        border-radius: 10px;
        padding: 9px 16px;
        color: {p['text']};
    }}
    QPushButton:hover {{ background: {p['hover']}; border-color: {AKCENT}; }}
    QPushButton:pressed {{ padding: 10px 15px 8px 17px; }}
    QPushButton#primary {{
        background: {AKCENT};
        color: #ffffff;
        border: 1px solid {AKCENT_CIEMNY};
        font-weight: 600;
    }}
    QPushButton#primary:hover {{ background: #35c56a; }}
    QPushButton#danger {{
        background: {p['danger']};
        color: #ffffff;
        border: 1px solid {p['danger_dark']};
    }}
    QPushButton#danger:hover {{ background: {p['danger_dark']}; }}
    QPushButton#flat {{ background: transparent; border: none; }}

    QTableView {{
        background: {p['table']};
        alternate-background-color: {p['table_alt']};
        gridline-color: {p['border']};
        border: 1px solid {p['border']};
        border-radius: 12px;
        selection-background-color: {AKCENT};
        selection-color: #ffffff;
    }}
    QHeaderView::section {{
        background: {p['panel2']};
        color: {p['text']};
        border: none;
        border-bottom: 1px solid {p['border']};
        padding: 8px;
        font-weight: 600;
    }}
    QTableView::item {{ padding: 6px; }}

    QTreeWidget {{
        background: {p['table']};
        border: 1px solid {p['border']};
        border-radius: 12px;
    }}
    QTreeWidget::item {{ padding: 5px; }}

    QCheckBox, QRadioButton {{ padding: 6px; spacing: 8px; }}
    QCheckBox::indicator, QRadioButton::indicator {{
        width: 18px; height: 18px;
        border-radius: 5px;
        border: 1px solid {p['border']};
        background: {p['input']};
    }}
    QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
        background: {AKCENT};
        border-color: {AKCENT_CIEMNY};
    }}

    QScrollArea {{ border: none; background: transparent; }}
    QScrollBar:vertical {{
        background: transparent; width: 10px; margin: 2px;
    }}
    QScrollBar::handle:vertical {{
        background: {p['border']}; border-radius: 5px; min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {AKCENT}; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}

    QStatusBar {{ background: transparent; color: {p['muted']}; }}
    QToolTip {{
        background: {p['panel']}; color: {p['text']};
        border: 1px solid {p['border']}; padding: 6px;
    }}
    QMessageBox {{ background: {p['bg']}; }}
    QTextEdit {{ background: {p['input']}; border: 1px solid {p['border']};
                border-radius: 10px; padding: 8px; }}
    """
