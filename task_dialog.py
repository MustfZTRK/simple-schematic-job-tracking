from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QComboBox, QPushButton, QDialogButtonBox

class TaskDialog(QDialog):
    def __init__(self, parent=None, title="", description="", status="Todo", category=""):
        super().__init__(parent)
        self.setWindowTitle("Edit Task")
        self.resize(400, 350)
        
        layout = QVBoxLayout(self)
        
        # Category
        layout.addWidget(QLabel("Category (e.g. Unity, SQL):"))
        self.category_edit = QLineEdit(category)
        layout.addWidget(self.category_edit)

        # Title
        layout.addWidget(QLabel("Title:"))
        self.title_edit = QLineEdit(title)
        layout.addWidget(self.title_edit)
        
        # Description
        layout.addWidget(QLabel("Description:"))
        self.desc_edit = QTextEdit(description)
        layout.addWidget(self.desc_edit)
        
        # Status
        layout.addWidget(QLabel("Status:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Todo", "In Progress", "Done"])
        self.status_combo.setCurrentText(status)
        layout.addWidget(self.status_combo)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def get_data(self):
        return {
            "category": self.category_edit.text(),
            "title": self.title_edit.text(),
            "description": self.desc_edit.toPlainText(),
            "status": self.status_combo.currentText()
        }
