"""Premium desktop stylesheet. Preview card stays white (Gmail canvas)."""

APP_STYLESHEET = """
QMainWindow, QWidget#Root {
    background: #0E1726;
    color: #E8EEF5;
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
}
QWidget#Sidebar {
    background: #121C2E;
    border-right: 1px solid #1E2A40;
}
QLabel#AppTitle {
    font-size: 18px;
    font-weight: 600;
    color: #F4F7FB;
    letter-spacing: 0.2px;
}
QLabel#AppSubtitle {
    color: #8A97AB;
    font-size: 12px;
}
QLabel#SectionTitle {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.1px;
    color: #6EBEED;
    padding: 16px 0 6px 0;
}
QLabel#FieldLabel {
    color: #A8B3C7;
    font-size: 12px;
}
QLineEdit#EmailLocal {
    border-top-right-radius: 0;
    border-bottom-right-radius: 0;
}
QLineEdit#EmailSuffix {
    background: #152033;
    color: #8A97AB;
    font-size: 13px;
    font-weight: 600;
    border: 1px solid #24344C;
    border-left: none;
    border-top-left-radius: 0;
    border-bottom-left-radius: 0;
    padding: 8px 10px;
}
QLineEdit {
    background: #0B1220;
    color: #F4F7FB;
    border: 1px solid #24344C;
    border-radius: 8px;
    padding: 8px 10px;
    selection-background-color: #1E4B8E;
}
QRadioButton {
    color: #E8EEF5;
    spacing: 8px;
    padding: 2px 0;
}
QRadioButton::indicator {
    width: 14px;
    height: 14px;
}
QWidget#PreviewPane {
    background: #D9E1EA;
}
QLabel#PreviewCaption {
    color: #4A5A70;
    font-size: 12px;
}
QPushButton {
    border: none;
    border-radius: 8px;
    padding: 10px 16px;
    font-weight: 600;
}
QPushButton#Primary {
    background: #008ACB;
    color: #FFFFFF;
}
QPushButton#Primary:hover {
    background: #0A9EE0;
}
QPushButton#Primary:pressed {
    background: #1E4B8E;
}
QPushButton#Secondary {
    background: #1E2A40;
    color: #E8EEF5;
    border: 1px solid #2B3D59;
}
QPushButton#Secondary:hover {
    background: #24344C;
}
QPushButton#Ghost {
    background: transparent;
    color: #8A97AB;
    border: 1px solid #2B3D59;
}
QScrollArea {
    border: none;
    background: transparent;
}
QStatusBar {
    background: #0E1726;
    color: #8A97AB;
}
"""
