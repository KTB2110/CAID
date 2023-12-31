import FreeCAD as App
import FreeCADGui as Gui
import Part
from FreeCAD import Base
from PySide2 import QtWidgets, QtGui, QtCore
from PySide2.QtWidgets import QFileDialog
from PIL import Image
import base64
import numpy as np
import cv2

from gpt4_integration import generate_chat_completion

def preprocess_image(image: np.ndarray) -> np.ndarray:
    image = np.fliplr(image)
    return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

def encode_image_to_base64(preprocessed_image: np.ndarray) -> str:
    success, buffer = cv2.imencode('.jpg', preprocessed_image)
    if not success:
        raise ValueError("Could not encode image to JPEG format.")

    encoded_image = base64.b64encode(buffer).decode('utf-8')
    return encoded_image

def compose_user_image_prompt_content(prompt, base64_images):

    user_dict = {}
    user_dict["role"] = "user"

    content = []
    content.append(
        {
        "type": "text",
        "text": prompt
        }
    )

    for base64_image in base64_images:
      content.append(
          {
              "type": "image_url",
              "image_url": {
                  "url": f"data:image/jpeg;base64,{base64_image}"
              }
          }
      )

    user_dict["content"] = content
    return user_dict
    
def process_command(command, conversation_history, preprocessed_image_list=None):
    messages = None
    try:
#         system_prompt = """
# You are a FreeCAD scripter. You will output and execute the Python code for the shape the user inputs

# If there are images uploaded, analyze the attached image(s), which displays multiple objects in a 3D space. The images are the different views of the SAME SET OF OBJECTS. Your task is to understand the 3D positional relationships and constraints between these objects, crucial for creating a CAD model. Follow these guidelines in your understanding:
# ​
# 1. **Identification of Objects**: Begin by understanding each visible object in the image using simple identifiers like 'Object A', 'Object B', etc.
# ​
# 2. **Positional Relationships**:
#    - Notice how each object is positioned in relation to the others, with ideas like 'to the left of', 'above', 'behind', etc.
#    - Focus on the orientation of objects, noting if they are parallel, perpendicular, or at specific angles to each other.
# ​
# 3. **Inferred Constraints**:
#    - Identify any potential CAD constraints such as coincident, concentric, parallel, perpendicular, tangent, distance, symmetric, angular, or fixed constraints.
# ​
# 4. **Dimensions and Proportional Relationships**:
#    - Estimate the dimensions of each object (height, width, depth).
#    - If possible, use any scale reference in the image to provide more precise measurements.
# ​
# 5. **Contact and Interaction**:
#    - Note any points where objects are touching, overlapping, or interlocking, and suggest appropriate constraints based on these interactions.
# ​
# 6. **Special Characteristics**:
#    - Notice observations of any significant curves, rounded edges, or unique geometric features that might influence constraints.
# ​
# Now keeping all this in memory, write FreeCAD code to generate this image in a CAD project.
#         """
        system_prompt = """
        You are a FreeCAD scripter. You will output and execute the Python code for the shape the user inputs. If the user has uploaded image(s), then you will look at the image(s) and write FreeCAD code that would create a 3d model of the image in FreeCAD.
        """
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history)
        # message = None
        if preprocessed_image_list:
            base64_images = [encode_image_to_base64(image) for image in preprocessed_image_list]
            message = compose_user_image_prompt_content(command, base64_images)
            messages.append(message)
        else:
            message = {"role": "user", "content": command}
            messages.append(message)
    
        response_text = generate_chat_completion(messages, max_tokens=4000)
    except Exception as e:
        return str(messages), str(e)
        
    return message, response_text

def ensure_active_document():
    if not App.ActiveDocument:
        App.newDocument("Unnamed")

class GPTCommandDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(GPTCommandDialog, self).__init__(parent)
        self.setWindowModality(QtCore.Qt.NonModal)  # Set the dialog to be non-modal
        self.init_ui()
        self.conversation_history = []
        self.image_paths = []

    def init_ui(self):
        # self.setWindowTitle("Design as a Conversation")
        # self.resize(600, 400)
        # self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint | QtCore.Qt.WindowMinimizeButtonHint)  # Remove question mark and add minimize button

        # self.verticalLayout = QtWidgets.QVBoxLayout(self)

        # self.scroll_area = QtWidgets.QScrollArea()
        # self.scroll_area.setWidgetResizable(True)
        # self.verticalLayout.addWidget(self.scroll_area)

        # self.scroll_widget = QtWidgets.QWidget()
        # self.scroll_area.setWidget(self.scroll_widget)
        # self.scroll_layout = QtWidgets.QVBoxLayout(self.scroll_widget)

        # self.label = QtWidgets.QLabel("Describe your part:")
        # self.verticalLayout.addWidget(self.label)

        # self.command_input = QtWidgets.QLineEdit()
        # self.verticalLayout.addWidget(self.command_input)

        # self.execute_button = QtWidgets.QPushButton("Execute")
        # self.execute_button.clicked.connect(self.execute_command)
        # self.verticalLayout.addWidget(self.execute_button)

        # self.undo_button = QtWidgets.QPushButton("Undo")
        # self.undo_button.clicked.connect(self.undo_last_command)
        # self.verticalLayout.addWidget(self.undo_button)

        # # Add a button to upload images
        # self.upload_image_button = QtWidgets.QPushButton("Upload Image")
        # self.upload_image_button.clicked.connect(self.upload_image)
        # self.verticalLayout.addWidget(self.upload_image_button)

        # # Container for image thumbnails
        # self.image_preview_layout = QtWidgets.QHBoxLayout()
        # self.verticalLayout.addLayout(self.image_preview_layout)
        self.setWindowTitle("Design as a Conversation")
        self.resize(600, 400)
        self.setStyleSheet("background-color: black; color: white;")  # Set background and text color
    
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.verticalLayout.addWidget(self.scroll_area)

        self.scroll_widget = QtWidgets.QWidget()
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_layout = QtWidgets.QVBoxLayout(self.scroll_widget)
        
        # Create a horizontal layout for input and buttons
        self.horizontalLayout = QtWidgets.QHBoxLayout()
    
        self.label = QtWidgets.QLabel("What do you want help with?")
        self.verticalLayout.addWidget(self.label)
    
        self.command_input = QtWidgets.QLineEdit()
        self.horizontalLayout.addWidget(self.command_input)
    
        self.execute_button = QtWidgets.QPushButton()
        self.execute_button.clicked.connect(self.execute_command)
        self.execute_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ArrowRight))
        self.execute_button.setIconSize(QtCore.QSize(24, 24))
        self.execute_button.setFixedSize(32, 32)  # Set the button to be square
        self.execute_button.setStyleSheet("""
            QPushButton {
                background-color: darkgray;
                font-weight: bold;
            }
        """)
        self.horizontalLayout.addWidget(self.execute_button)
    
        # Create a circular button for image upload
        self.upload_image_button = QtWidgets.QPushButton()
        self.upload_image_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DirOpenIcon))
        self.upload_image_button.setIconSize(QtCore.QSize(24, 24))  # Adjust icon size as needed
        self.upload_image_button.setFixedSize(32, 32)  # Adjust button size as needed
        self.upload_image_button.setStyleSheet("QPushButton { background-color: darkgray; border-radius: 16px; }")  # Set the button background to light gray and make it circular
        self.upload_image_button.clicked.connect(self.upload_image)
        self.horizontalLayout.addWidget(self.upload_image_button)

        self.undo_button = QtWidgets.QPushButton("Undo")
        self.undo_button.clicked.connect(self.undo_last_command)
        self.undo_button.setStyleSheet("""
            QPushButton {
                background-color: darkgray;
                color: black;
                font-weight: bold;
            }
        """)
        self.horizontalLayout.addWidget(self.undo_button)
        
        # Add the horizontal layout to the vertical layout
        self.verticalLayout.addLayout(self.horizontalLayout)
    
        # Container for image thumbnails
        self.image_preview_layout = QtWidgets.QHBoxLayout()
        self.verticalLayout.addLayout(self.image_preview_layout)

    def execute_command(self):
        command = self.command_input.text()
        if not command:
            App.Console.PrintError("No command found.\n")
            return

        try:
            image_list = []
            if len(self.image_paths) > 0:
                for filename in self.image_paths:
                    img = Image.open(filename)
                    image_list.append(img)


            if len(image_list) > 0:
                preprocessed_image_list = [preprocess_image(image=image) for image in image_list]
                message_text, response_text = process_command(command=command, conversation_history=self.conversation_history, preprocessed_image_list=preprocessed_image_list)
                # App.Console.PrintMessage(f"# Message: {message_text}\n")
            else:
                message_text, response_text = process_command(command=command, conversation_history=self.conversation_history)
                # App.Console.PrintMessage(f"# Message: {message_text}\n")
                
            
            self.conversation_history.append(message_text)

            # Display user input in the scrollable area
            user_label = QtWidgets.QLabel(f"USER INPUT")
            user_label.setFont(QtGui.QFont("Arial", 9, QtGui.QFont.Bold))
            self.scroll_layout.addWidget(user_label)
            
            user_command = QtWidgets.QLabel(f"{command}")
            user_command.setFont(QtGui.QFont("Arial", 9))
            user_command.setWordWrap(True)
            self.scroll_layout.addWidget(user_command)

            # Scroll to the bottom of the scrollable area
            self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())

            self.command_input.clear()

            ensure_active_document()

            # Check if the response contains code
            # if "```python" in response_text and "\n```" in response_text:
            #     # Split the response into description and code parts
            #     _, code = response_text.split("```python\n", 1)
            #     code, _ = code.split("\n```", 1)

            #     # Print the code in the console
            #     App.Console.PrintMessage(f"{code}\n")

            #     # Execute the generated code in the Python environment
            #     exec(code, {"App": App, "Part": Part, "Base": Base})

            description = "Error occured when accessing the API. Please try again"
            if "```python" in response_text and "\n```" in response_text:
                # Split the response into description, code, and any text after the code
                parts = response_text.split("```python")
                description = parts[0]  # Text before the code block
            
                # Further split the second part to separate the code from text after the code block
                code_with_after_text = parts[1].split("\n```", 1)
                code = code_with_after_text[0]  # The actual code
                after_text = code_with_after_text[1] if len(code_with_after_text) > 1 else ""  # Text after the code block

                # Print the code in the console
                gpt_label = QtWidgets.QLabel(f"GPT4")
                gpt_label.setFont(QtGui.QFont("Arial", 9, QtGui.QFont.Bold))
                gpt_label.setStyleSheet("color: rgb(0, 128, 0);")
                self.scroll_layout.addWidget(gpt_label)
                
                gpt_command = QtWidgets.QLabel(f"{description}I have added the code in the console.\nLet me know if you have any further questions!")
                gpt_command.setFont(QtGui.QFont("Arial", 9))
                gpt_command.setStyleSheet("color: rgb(0, 156, 0);")
                gpt_command.setWordWrap(True)
                self.scroll_layout.addWidget(gpt_command)
                
                App.Console.PrintMessage(f"{code}\n")

                # Execute the generated code in the Python environment
                exec(code, {"App": App, "Part": Part, "Base": Base})
            else:
                gpt_label = QtWidgets.QLabel(f"GPT4")
                gpt_label.setFont(QtGui.QFont("Arial", 9, QtGui.QFont.Bold))
                gpt_label.setStyleSheet("color: rgb(0, 156, 0);")
                self.scroll_layout.addWidget(gpt_label)
                
                gpt_command = QtWidgets.QLabel(f"{response_text}")
                gpt_command.setFont(QtGui.QFont("Arial", 9))
                gpt_command.setStyleSheet("color: rgb(0, 156, 0);")
                gpt_command.setWordWrap(True)
                self.scroll_layout.addWidget(gpt_command)
                
                App.Console.PrintMessage(f"No Code Was Generated\n")
           
        
        except Exception as e:
                        App.Console.PrintError(f"Error: {str(e)}\n")
            
    def undo_last_command(self):
        if App.ActiveDocument is not None:
            if App.ActiveDocument.UndoCount > 0:
                App.ActiveDocument.undo()
                App.Console.PrintMessage(f"Undid the last command.\n")
            else:
                App.Console.PrintError(f"No actions to undo.\n")

    def upload_image(self):
        # Allow multiple selection of image files
        file_dialog = QtWidgets.QFileDialog(self)
        file_dialog.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Images (*.png *.xpm *.jpg *.jpeg *.bmp *.gif)")

        # Execute the dialog and check if the user has accepted the selection
        if file_dialog.exec_() == QtWidgets.QDialog.Accepted:
            image_files = file_dialog.selectedFiles()
            self.show_selected_images(image_files)

    def show_selected_images(self, image_files):
        # Clear the current thumbnails
        while self.image_preview_layout.count():
            child = self.image_preview_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for image_file in image_files:
            pixmap = QtGui.QPixmap(image_file)
            label = QtWidgets.QLabel()
            label.setPixmap(pixmap.scaled(64, 64, QtCore.Qt.KeepAspectRatio))  # Resize to thumbnail size
            self.image_preview_layout.addWidget(label)

        self.image_paths = image_files


def show_gpt_command_dialog():
    dialog = GPTCommandDialog(Gui.getMainWindow())
    dialog.show()

from PySide2.QtCore import QCoreApplication, QMetaObject, QTimer

def delayed_show_dialog():
    dialog = GPTCommandDialog(Gui.getMainWindow())
    dialog.show()

timer = QTimer()
timer.setSingleShot(True)
timer.timeout.connect(delayed_show_dialog)
timer.start(0)
