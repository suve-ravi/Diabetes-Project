from docx import Document
from docx.shared import Inches
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel,
    QInputDialog, QDialog, QComboBox, QGridLayout, QLineEdit, QMessageBox, QFileDialog
)
from PyQt5.QtGui import QFont
import sys
import os
import numpy as np
import json

class BarChartCanvas(FigureCanvas):
    def __init__(self, parent=None, num_questions=21, answers=None):
        fig, self.ax = plt.subplots(figsize=(6, 6))
        super().__init__(fig)
        self.setParent(parent)
        self.num_questions = num_questions
        self.answers = answers or ["Low"] * self.num_questions
        self.answers.append("Low")
        self.draw_chart()

    def draw_chart(self):
        self.ax.clear()
        y_labels = [f"Q{i+1}" for i in range(len(self.answers)-1)]
        y_labels.append("Prediction")
        y_pos = np.arange(len(self.answers))

        colors = {
            "G": "green",
            "Y": "yellow",
            "R": "red",
            "B": "blue",
            "P": "pink",
            "": "gray"   # unanswered stays gray
        }

        # Define colors for risk levels
        #colors = {'Low': 'yellow', 'Medium': 'orange', 'High': 'red'}
        bar_height = 1.0  # Full height per unit to eliminate gaps

        for i, risk in enumerate(self.answers):
            self.ax.barh(
                y_pos[i],
                10,  # Arbitrary same width
                height=bar_height,
                color=colors.get(risk, 'gray'),
                edgecolor='black',
                align='center'
            )

        self.ax.set_yticks(y_pos)
        self.ax.set_yticklabels(y_labels)
        self.ax.set_xlim(0, 10)
        self.ax.set_ylim(-0.5, len(self.answers) - 0.5)
        self.ax.invert_yaxis()  # Q1 at top
        #self.ax.set_title('Risk Levels')
        self.ax.set_xticks([])

        self.draw()

    """
    def draw_chart(self):
        self.ax.clear()
        color_map = {"Low": "yellow", "Medium": "orange", "High": "red"}
        for i, level in enumerate(self.answers):
            self.ax.barh(i, 1, color=color_map[level], edgecolor='black')
        self.ax.set_xlim(0, 1)
        self.ax.set_yticks(range(self.num_questions))
        self.ax.set_yticklabels([f"Q{i+1}" for i in range(self.num_questions)])
        self.ax.set_xticks([])
        self.ax.invert_yaxis()
        #self.ax.set_title("Risk Levels")
        self.draw()
    """

    def update_answers(self, new_answers):
        self.answers = new_answers
        self.draw_chart()

    def save_chart_image(self, filename="chart.png"):
        self.figure.savefig(filename)


class SurveyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VitaScreen")
        self.resize(1000,1000)

        script_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(script_dir, 'VitaScreenDiabetesQuestions.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            self.questions = json.load(f)["questions"]

        self.answers = [""] * (len(self.questions) + 1)

        self.name_input = QLineEdit()
        self.health_id_input = QLineEdit()

        self.chart = BarChartCanvas(self, answers=self.answers)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.create_top_inputs()
        self.create_question_buttons()
        self.layout.addWidget(self.chart)
        self.create_action_buttons()

    def create_top_inputs(self):
        form_layout = QGridLayout()
        form_layout.addWidget(QLabel("Name:"), 0, 0)
        form_layout.addWidget(self.name_input, 0, 1)
        form_layout.addWidget(QLabel("Health Card ID:"), 1, 0)
        form_layout.addWidget(self.health_id_input, 1, 1)
        self.layout.addLayout(form_layout)

    def create_question_buttons(self):
        question_layout = QGridLayout()
        for i in range(len(self.questions)):
            button = QPushButton(f"Q{i+1}")
            button.clicked.connect(lambda _, idx=i: self.ask_question(idx))
            question_layout.addWidget(button, i // 5, i % 5)
        self.layout.addLayout(question_layout)

    def create_action_buttons(self):
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reset_answers)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_report)

        quit_btn = QPushButton("Quit")
        quit_btn.clicked.connect(self.quit_application)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(quit_btn)

        self.layout.addLayout(button_layout)

    def ask_question(self, idx):
        q_data = self.questions[idx]
        question_text = q_data.get("question", f"Question {idx+1}")

        options_dict = q_data.get("possible_answers", {})
        if not isinstance(options_dict, dict):
            print(f"Error: possible_answers is {type(options_dict)} for question {idx+1}")
            return

        # Build a list of answer strings for the dropdown
        options = []
        for val in options_dict.values():
            if isinstance(val, dict):
                options.append(val.get("answer", ""))
            elif isinstance(val, str):
                options.append(val)
        
        # Show dropdown
        choice, ok = QInputDialog.getItem(
            self,
            f"Answer for Q{idx+1}",
            question_text,
            options,
            editable=False
        )

        if ok and choice:
            # Map the selected answer back to its color code
            color = "G"  # default fallback
            for val in options_dict.values():
                if isinstance(val, dict) and val.get("answer") == choice:
                    color = val.get("color", "R")
                    break
                elif isinstance(val, str) and val == choice:
                    color = "G"

            # Save the color in answers
            self.answers[idx] = color

            # Update the chart
            self.chart.update_answers(self.answers)

    def reset_answers(self):
        self.answers = [""] * (len(self.questions)+1)
        self.chart.update_answers(self.answers)

    def save_report(self):
        name = self.name_input.text().strip()
        hcid = self.health_id_input.text().strip()
        if not name or not hcid:
            QMessageBox.warning(self, "Missing Info", "Please enter Name and Health Card ID before saving.")
            return

        save_path = QFileDialog.getSaveFileName(self, "Save Word Report", "", "Word Document (*.docx)")[0]
        if not save_path:
            return

        if not save_path.endswith(".docx"):
            save_path += ".docx"

        chart_img = "temp_chart.png"
        self.chart.save_chart_image(chart_img)

        doc = Document()
        doc.add_heading("Diabetic Risk Screening Report", 0)
        doc.add_paragraph(f"Name: {name}")
        doc.add_paragraph(f"Health Card ID: {hcid}")
        doc.add_picture(chart_img, width=Inches(5.5))
        doc.save(save_path)

        os.remove(chart_img)
        QMessageBox.information(self, "Saved", f"Report saved to {save_path}")

    def quit_application(self):
        reply = QMessageBox.question(self, "Quit", "Do you want to save before quitting?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        if reply == QMessageBox.Yes:
            self.save_report()
            QApplication.quit()
        elif reply == QMessageBox.No:
            QApplication.quit()
        # Cancel does nothing


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SurveyApp()
    window.show()
    sys.exit(app.exec_())