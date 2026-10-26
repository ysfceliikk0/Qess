# Universal File Drop Catcher - Qess

This project is a desktop utility application designed to improve file management workflow. It continuously monitors specific directories (such as Downloads, Quick Share, and Phone Link folders) and temporarily stores incoming files in an interactive dropzone located at the edge of the screen.

## Features

* File Monitoring: Automatically detects new incoming files using file system events, while ignoring temporary or incomplete downloads.
* Interactive Dropzone: A hidden tray at the edge of the screen that expands upon mouse hover, displaying the captured files.
* Drag and Drop Integration: Files can be dragged directly from the dropzone into other applications, directories, or the desktop.
* Native Sharing: Utilizes the native sharing interface of the operating system to quickly share captured files.
* Customization: Includes a settings menu to adjust the screen edge position, interface themes, and display duration.
* System Integration: Runs in the background via the system tray and can be configured to start automatically on system boot.

## Technologies Used

* Python: The core programming language used for the application logic.
* PyQt6: Used for building the graphical user interface, handling animations, drag-and-drop mechanics, and system tray operations.
* Watchdog: Implemented to monitor file system events in real-time across multiple directories.
* Winsdk: Used on Windows environments to trigger the native OS share dialog.

## Installation and Setup

1. Clone this repository to your local machine.
2. Install the required dependencies using pip:
   pip install -r requirements.txt
3. Run the application:
   python main.py

To build a standalone executable file, you can use PyInstaller:
pyinstaller --noconsole --onefile --windowed main.py
```text
universal-file-drop-catcher/
├── main.py        
├── config.json   
├── requirements.txt   
├── .gitignore        
└── README.md     
```
