# 🖨️ AutoPrint Pro — Automatic Email Print Server

> **Send an email → File prints automatically!**  
> No need to be near the computer. Just email the file and it prints within 15 seconds.

---

## 📋 What Is This?

AutoPrint Pro is a **Windows-based automatic print server** that monitors a Gmail inbox and prints any attached PDF, JPG, or PNG files automatically — without any manual intervention.

Built specifically for **LIC (Life Insurance Corporation) agents** but works for anyone who needs to print documents remotely.

---

## ✨ Features

| Feature | Details |
|---|---|
| 📧 **Email to Print** | Send email with attachment → prints automatically |
| 🧠 **Smart Detection** | Auto detects LIC receipts, Aadhaar, PAN, certificates |
| 📐 **Auto Orientation** | Always prints portrait — fixes sideways photos |
| ✂️ **Smart Crop** | Detects document edges even on messy backgrounds |
| 🎨 **Colour/BW** | Default colour — switch with simple commands |
| 📝 **Email Commands** | Write `black`, `2 copies`, `landscape`, `b5` in email body |
| ✅ **Auto Reply** | Sender gets confirmation email after every print |
| ❌ **Failure Alert** | Alert email if printing fails |
| 🔕 **Silent Running** | Runs completely hidden in background |
| 🚀 **Auto Start** | Starts automatically when Windows boots |

---

## 🎯 How It Works

```
Father sends email                Server detects email
with attachment         ──────►   within 15 seconds
📎 document.pdf                        │
                                       ▼
                               Detects document type
                               LIC? → B5 Colour
                               Other? → A4 Colour
                                       │
                                       ▼
                               Fixes orientation
                               Crops if needed
                               Enhances if faded
                                       │
                                       ▼
                               🖨️ Prints automatically!
                                       │
                                       ▼
                               ✅ Sends confirmation
                                  email to sender
```

---

## 📧 Email Commands

Write these in the email body to override default settings:

| Command | Result |
|---|---|
| *(nothing written)* | A4 Colour Portrait (default) |
| `black` or `black and white` | Print in Black & White |
| `landscape` | Print in Landscape |
| `2 copies` or `3 copies` | Print multiple copies |
| `b5` | Print on B5 paper |
| `a3` | Print on A3 paper |
| `black 2 copies` | B&W + 2 copies |

Hindi commands also work: `black mein karo`, `do copy chahiye` etc.

---

## 🔍 Auto Document Detection

| Document | Auto Settings |
|---|---|
| LIC Premium Receipt | B5 Colour (direct print) |
| Aadhaar Card | A4 Colour |
| PAN Card | A4 Colour |
| Birth/Death Certificate | A4 Colour |
| Passport | A4 Colour |
| Bank Statement | A4 Colour |
| Any other document | A4 Colour (default) |

---

## 🛠️ Requirements

- Windows 10/11
- Python 3.8 or higher → [Download](https://python.org)
- Tesseract OCR → [Download](https://github.com/UB-Mannheim/tesseract/wiki)
- SumatraPDF → [Download](https://www.sumatrapdfreader.org/download-free-pdf-viewer)
- Gmail account with 2-Step Verification enabled

---

## ⚙️ Installation

### Step 1 — Clone or Download
```bash
git clone https://github.com/yourusername/autoprint-pro.git
```
Or click **Code → Download ZIP** and extract to `C:\autoprint_pro\`

### Step 2 — Install Python Libraries
```cmd
pip install PyMuPDF reportlab Pillow pytesseract pywin32 numpy opencv-python
```

### Step 3 — Setup Gmail App Password
1. Go to [myaccount.google.com](https://myaccount.google.com)
2. Security → 2-Step Verification → App Passwords
3. Create new App Password
4. Copy the 16 character code

### Step 4 — Configure
```cmd
cd C:\autoprint_pro\autoprint_pro\config
copy config.example.py config.py
notepad config.py
```

Fill in your details:
```python
EMAIL_ADDRESS      = "your_print_server@gmail.com"
EMAIL_APP_PASSWORD = "xxxx xxxx xxxx xxxx"
ALLOWED_SENDERS    = ["your_email@gmail.com"]
PRINTER_NAME       = "Your Printer Name"
```

To find your printer name:
```cmd
python -c "import win32print; [print(p[2]) for p in win32print.EnumPrinters(2)]"
```

### Step 5 — Test
```cmd
cd C:\autoprint_pro
python main.py --once
```
Should show: `IMAP login successful`

### Step 6 — Setup Auto Start
Right click `setup_autostart.bat` → **Run as administrator**

✅ Server now starts automatically with Windows — completely hidden!

---

## 📁 Project Structure

```
autoprint_pro/
├── main.py                    ← Main server
├── config/
│   ├── config.example.py      ← Copy this → rename to config.py
│   └── config.py              ← Your settings (never upload to GitHub!)
├── scripts/
│   ├── email_handler.py       ← Gmail IMAP polling
│   ├── command_parser.py      ← Email body command reading
│   ├── document_detector.py   ← LIC/document type detection
│   ├── document_processor.py  ← Orientation, crop, enhancement
│   ├── smart_crop.py          ← OpenCV document crop
│   ├── print_manager.py       ← Windows printer integration
│   ├── notifier.py            ← Email confirmation/alerts
│   ├── job_logger.py          ← CSV print history
│   └── logger.py              ← System logs
├── downloads/                 ← Raw downloaded attachments
├── processed/                 ← Print-ready PDFs
└── logs/                      ← System logs + print history
```

---

## 🖥️ Usage

```cmd
python main.py          # Run server continuously
python main.py --once   # Run once (for testing)
```

---

## 🔧 Troubleshooting

**"No new messages found" — but I sent an email**
- Make sure attachment is sent with paperclip 📎 button
- Do NOT paste/insert image in email body
- Check sender email is in `ALLOWED_SENDERS` list

**Printing in wrong colour**
- Make sure SumatraPDF is installed
- Check `PRINTER_NAME` matches exactly

**Server not starting automatically**
- Run `setup_autostart.bat` as Administrator
- Check Task Manager → Details → `python.exe` should be visible

---

## 📊 Print History

All print jobs are logged to:
```
autoprint_pro/logs/print_jobs.csv
```

Open with Excel to see full history with dates, files, status.

---

## 🤝 Contributing

Pull requests are welcome! Feel free to:
- Add support for more document types
- Improve smart crop algorithm
- Add new email command keywords
- Support other operating systems

---

## 📄 License

MIT License — free to use, modify and distribute.

---

## 👨‍💻 Author

Built with ❤️ for LIC agents and anyone who needs automatic printing.

---

## ⭐ If This Helped You

Give it a star on GitHub! It helps others find this project.
