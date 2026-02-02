### 🚀 Key Features

<img width="852" height="632" alt="{00613152-B510-42B9-9D4A-9B054969928C}" src="https://github.com/user-attachments/assets/49cbf4bb-e66f-46a4-b455-f5afdc66e312" />


* **Raw Disk Access:** Uses low-level Windows API (`\\.\PhysicalDrive`) to bypass OS file system limitations for deep-sector carving.
* **Signature-Based Recovery:** Scans for hex signatures `0xFFD8FFE0` and `0xFFD8FFE1` to identify valid JPEG headers.
* **Smart EXIF Sorting:** Automatically reads `DateTimeOriginal` metadata to organize recovered files into `YYYY-MM-DD` folders.
* **Sequential Reconstruction:** Employs logic to reassemble fragmented headers and maintain file integrity.
* **Responsive UI:** Built with a multi-threaded PyQt6 interface to ensure the application remains responsive during heavy disk I/O operations.
* **Automatic Elevation:** Includes built-in logic to request Administrator privileges required for physical drive access.

---

### 🛠 Technical Stack

* **Language:** Python 3.x
* **GUI:** PyQt6
* **Metadata:** piexif
* **Low-level I/O:** ctypes & os (Windows API)

---

### 💻 Installation

1. **Clone the repository:**
```bash
git clone https://github.com/DRCRecoveryData/JPEG-Carver-Pro.git
cd JPEG-Carver-Pro

```


2. **Install required dependencies:**
```bash
pip install -r requirements.txt

```



---

### 📖 How to Use

1. **Launch the app:** Run `python JPEG-Carver-Pro.py` (ensure you are on Windows).
2. **Select Source:** Choose the target **Physical Drive** from the dropdown menu.
3. **Set Destination:** Pick a folder where you want the carved images to be saved.
4. **Start Carving:** Click **START**. The tool will scan the drive and sort photos by date in real-time.
5. **Monitor Progress:** Use the built-in log viewer and progress bar to track the recovery status.

---

### ⚠️ Disclaimer

This tool is provided for forensic and data recovery purposes. Direct hardware access is powerful; always ensure you have the proper authorization to scan the target media. The author is not responsible for any data loss resulting from improper use.
