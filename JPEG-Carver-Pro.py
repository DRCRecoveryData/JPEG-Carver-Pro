import sys
import os
import ctypes
import piexif
import shutil
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QProgressBar, 
                             QComboBox, QTextEdit, QMessageBox, QFileDialog)
from PyQt6.QtCore import QThread, pyqtSignal, Qt

# --- Auto-Admin Elevation ---
def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

if not is_admin():
    # Elevates privileges to access \\.\PhysicalDrive
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

def get_drive_size(disk_num):
    """Detects total physical drive bytes using Windows API."""
    try:
        device_path = f"\\\\.\\PhysicalDrive{disk_num}"
        handle = ctypes.windll.kernel32.CreateFileW(
            device_path, 0x80000000, 0x00000001 | 0x00000002,
            None, 3, 0, None
        )
        if handle == -1: return 0
        disk_size = ctypes.c_longlong()
        res = ctypes.windll.kernel32.DeviceIoControl(
            handle, 0x0007405C, None, 0,
            ctypes.byref(disk_size), ctypes.sizeof(disk_size),
            ctypes.byref(ctypes.c_ulong()), None
        )
        ctypes.windll.kernel32.CloseHandle(handle)
        return disk_size.value if res else 0
    except: return 0

# --- Worker Thread ---
class CarverWorker(QThread):
    progress_update = pyqtSignal(float, int)
    log_update = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, disk_num, output_path):
        super().__init__()
        self.disk_num = disk_num
        self.output_path = output_path
        self.running = True
        # Tracks naming index for each specific date folder
        self.date_counters = {} 

    def get_exif_date(self, image_bytes):
        """Extracts date from EXIF or returns current time."""
        try:
            exif_dict = piexif.load(image_bytes)
            date_str = exif_dict.get("Exif", {}).get(36867).decode('utf-8')
            return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
        except:
            return datetime.now()

    def run(self):
        device_path = f"\\\\.\\PhysicalDrive{self.disk_num}"
        total_bytes = get_drive_size(self.disk_num) or (1024**3)
        SOI_MARKERS = [b'\xff\xd8\xff\xe0', b'\xff\xd8\xff\xe1']
        CHUNK_SIZE = 1024 * 1024  
        
        try:
            fd = os.open(device_path, os.O_RDONLY | os.O_BINARY)
            file_count = 0
            remainder = b""
            bytes_scanned = 0
            
            while bytes_scanned < total_bytes and self.running:
                try:
                    raw_chunk = os.read(fd, CHUNK_SIZE)
                    if not raw_chunk: break
                except OSError:
                    os.lseek(fd, 512, os.SEEK_CUR)
                    bytes_scanned += 512
                    continue
                
                data = remainder + raw_chunk
                bytes_scanned += len(raw_chunk)
                search_pos = 0

                while True:
                    found_idx = -1
                    for marker in SOI_MARKERS:
                        m_pos = data.find(marker, search_pos)
                        if m_pos != -1 and (found_idx == -1 or m_pos < found_idx):
                            found_idx = m_pos
                    
                    if found_idx == -1:
                        remainder = data[-4:] 
                        break
                    
                    next_idx = -1
                    for marker in SOI_MARKERS:
                        n_pos = data.find(marker, found_idx + 4)
                        if n_pos != -1 and (next_idx == -1 or n_pos < next_idx):
                            next_idx = n_pos
                    
                    if next_idx != -1:
                        jpeg_data = data[found_idx:next_idx]
                        
                        # Size filter to skip empty headers
                        if len(jpeg_data) > 1024:
                            # 1. Get folder by date
                            photo_date = self.get_exif_date(jpeg_data)
                            date_folder = photo_date.strftime('%Y-%m-%d')
                            target_dir = os.path.join(self.output_path, date_folder)
                            os.makedirs(target_dir, exist_ok=True)
                            
                            # 2. Sequential Name Logic
                            if date_folder not in self.date_counters:
                                self.date_counters[date_folder] = 1
                            
                            new_name = f"{self.date_counters[date_folder]:04d}.JPG"
                            dest_path = os.path.join(target_dir, new_name)
                            
                            with open(dest_path, 'wb') as f:
                                f.write(jpeg_data)
                            
                            file_count += 1
                            self.log_update.emit(f"⚡ Saved: {date_folder}/{new_name} ({len(jpeg_data)//1024} KB)")
                            self.date_counters[date_folder] += 1
                        
                        search_pos = next_idx
                    else:
                        remainder = data[found_idx:]
                        break
                
                prog = min(100.0, (bytes_scanned / total_bytes) * 100)
                self.progress_update.emit(prog, file_count)

            os.close(fd)
        except Exception as e:
            self.log_update.emit(f"🛑 Error: {str(e)}")
        
        self.finished.emit()

    def stop(self):
        self.running = False

# --- Main App ---
class PhotoCarverApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Photo Carver Pro")
        self.setMinimumSize(850, 600)
        self.save_path = os.path.join(os.environ['USERPROFILE'], 'Pictures', 'Carved')
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Style sheet
        self.setStyleSheet("""
            QMainWindow { background-color: #0d0d0d; }
            QLabel { color: #00ff9d; font-family: 'Segoe UI'; font-weight: bold; }
            QComboBox { background-color: #1a1a1a; color: white; border: 1px solid #333; padding: 5px; border-radius: 3px; }
            QPushButton { background-color: #222; color: #eee; border: 1px solid #444; padding: 10px; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #333; border-color: #00ff9d; }
            QTextEdit { background-color: #050505; color: #00e676; font-family: 'Consolas'; font-size: 11px; border: 1px solid #222; }
            QProgressBar { border: 1px solid #333; border-radius: 5px; text-align: center; color: white; background: #111; height: 15px;}
            QProgressBar::chunk { background-color: #6200ea; }
        """)

        # Drive Selection
        drive_row = QHBoxLayout()
        drive_row.addWidget(QLabel("SOURCE DRIVE:"))
        self.drive_combo = QComboBox()
        for i in range(10):
            sz = get_drive_size(i)
            if sz > 0:
                self.drive_combo.addItem(f"Physical Drive {i} ({sz/(1024**3):.2f} GB)", i)
        drive_row.addWidget(self.drive_combo, 1)
        layout.addLayout(drive_row)

        # Path Selection
        path_row = QHBoxLayout()
        self.path_label = QLabel(f"DESTINATION: {self.save_path}")
        path_row.addWidget(self.path_label, 1)
        btn_path = QPushButton("CHANGE FOLDER")
        btn_path.clicked.connect(self.pick_folder)
        path_row.addWidget(btn_path)
        layout.addLayout(path_row)

        # START Button
        self.start_btn = QPushButton("START")
        self.start_btn.setFixedHeight(45)
        self.start_btn.setStyleSheet("background-color: #00ff9d; color: black; font-size: 14px;")
        self.start_btn.clicked.connect(self.start_scan)
        layout.addWidget(self.start_btn)

        # STOP Button (Red)
        self.stop_btn = QPushButton("STOP")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setFixedHeight(45)
        self.stop_btn.setStyleSheet("background-color: #ff1744; color: white; font-size: 14px;")
        self.stop_btn.clicked.connect(self.stop_scan)
        layout.addWidget(self.stop_btn)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.log_viewer = QTextEdit()
        self.log_viewer.setReadOnly(True)
        layout.addWidget(self.log_viewer)

    def pick_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Select Save Location")
        if path:
            self.save_path = path
            self.path_label.setText(f"DESTINATION: {self.save_path}")

    def start_scan(self):
        if self.drive_combo.count() == 0:
            QMessageBox.warning(self, "Error", "No physical drives detected. Re-run as Admin.")
            return
        self.log_viewer.clear()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.worker = CarverWorker(self.drive_combo.currentData(), self.save_path)
        self.worker.progress_update.connect(self.update_progress)
        self.worker.log_update.connect(self.log_viewer.append)
        self.worker.finished.connect(self.on_done)
        self.worker.start()

    def update_progress(self, percent, count):
        self.progress_bar.setValue(int(percent))
        self.setWindowTitle(f"Carving: {count} found ({int(percent)}%)")

    def stop_scan(self):
        if hasattr(self, 'worker'):
            self.worker.stop()

    def on_done(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        QMessageBox.information(self, "Complete", "The drive scan is finished.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = PhotoCarverApp()
    win.show()
    sys.exit(app.exec())