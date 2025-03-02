import pdfplumber
import re
import tkinter as tk
from tkinter import ttk, filedialog
import pyperclip
from threading import Thread

def calculate_percentage_diff(mean, median):
    try:
        mean_val = float(mean)
        median_val = float(median)
        if median_val == 0:
            return 0
        return abs((mean_val - median_val) / median_val) * 100
    except:
        return 0

def evaluate_coverage(value, thresholds, is_percent=False):
    try:
        value = float(value.replace('%', '')) if is_percent else float(value)
        for threshold, emoji in thresholds:
            if value >= threshold:
                return emoji
        return "🔴"
    except:
        return "⚪"

def extract_coverage_data(pdf_path, progress_callback=None):
    data = {
        'avg': "Bulunamadı",
        'median': "Bulunamadı",
        'min_100x': "Bulunamadı",
        'min_500x': "Bulunamadı"
    }
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            
            # Average coverage
            avg_match = re.search(r"Average coverage\s*[\|:]?\s*(\d+\.\d+)", text)
            if avg_match:
                data['avg'] = avg_match.group(1)
            
            # Median coverage
            median_match = re.search(r"Median coverage\s*[\|:]?\s*(\d+\.\d+)", text)
            if median_match:
                data['median'] = median_match.group(1)
            
            # 100x Coverage
            min_100x_match = re.search(r"100\s+(\d+\.\d{2})", text)
            if min_100x_match:
                data['min_100x'] = min_100x_match.group(1)
            
            # 500x Coverage
            min_500x_match = re.search(r"500\s+(\d+\.\d{2})", text)
            if min_500x_match:
                data['min_500x'] = min_500x_match.group(1)
    
    if progress_callback:
        progress_callback()
    
    return data

def format_for_whatsapp(results):
    formatted_text = "📊 *COVERAGE ÖZET*\n\n"
    
    for idx, (file_path, res) in enumerate(results, 1):
        file_name = file_path.split("/")[-1]
        diff_percent = calculate_percentage_diff(res['avg'], res['median'])
        
        # Emoji atamaları
        avg_emoji = "🟢" if diff_percent < 20 else "🟡" if diff_percent < 50 else "🔴"
        cov_100x_emoji = evaluate_coverage(res['min_100x'], [(95, "🟢"), (85, "🟡")], True)
        cov_500x_emoji = evaluate_coverage(res['min_500x'], [(90, "🟢"), (70, "🟡")], True)
        
        # Özet satırı
        summary = f"Ortalama/Medyan %{diff_percent:.1f} farklı {avg_emoji}"
        
        formatted_text += (
            f"▫️ *Dosya {idx}:* `{file_name}`\n"
            f"   {avg_emoji} Ortalama: `{res['avg']}`\n"
            f"   {avg_emoji} Medyan: `{res['median']}`\n"
            f"   {cov_100x_emoji} 100x Coverage: `{res['min_100x']}%`\n"
            f"   {cov_500x_emoji} 500x Coverage: `{res['min_500x']}%`\n"
            f"   📌 *Özet:* {summary}\n\n"
        )
    
    return formatted_text

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NGS Coverage Analyzer v3.0")
        self.geometry("900x600")
        self.progress = ttk.Progressbar(self, orient="horizontal", length=400, mode="determinate")
        self.text_box = tk.Text(self, wrap=tk.WORD, font=("Consolas", 10), height=20)
        self.btn_frame = ttk.Frame(self)
        self.setup_ui()
        
    def setup_ui(self):
        # Header
        ttk.Label(self, text="🔬 COVERAGE REPORT ÖZETLEYİCİ", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Butonlar
        ttk.Button(self.btn_frame, text="📂 PDF Yükle", command=self.start_processing).pack(side=tk.LEFT, padx=5)
        self.copy_btn = ttk.Button(self.btn_frame, text="📋 Panoya Kopyala", state=tk.DISABLED, command=self.copy_results)
        self.copy_btn.pack(side=tk.LEFT, padx=5)
        self.btn_frame.pack(pady=5)
        
        # İlerleme Çubuğu
        self.progress.pack(pady=10)
        
        # Sonuç Ekranı
        self.text_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
    def start_processing(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])
        if not file_paths:
            return
        
        self.progress["value"] = 0
        self.progress["maximum"] = len(file_paths)
        Thread(target=self.process_files, args=(file_paths,), daemon=True).start()
        
    def process_files(self, file_paths):
        results = []
        for idx, path in enumerate(file_paths, 1):
            data = extract_coverage_data(path, lambda: self.update_progress(idx))
            results.append((path, data))
        
        formatted_text = format_for_whatsapp(results)
        self.text_box.delete(1.0, tk.END)
        self.text_box.insert(tk.END, formatted_text)
        self.copy_btn.config(state=tk.NORMAL)
        
    def update_progress(self, value):
        self.progress["value"] = value
        self.update_idletasks()
        
    def copy_results(self):
        pyperclip.copy(self.text_box.get(1.0, tk.END))
        ttk.Label(self, text="✔️ Panoya kopyalandı! (Ctrl+V ile WhatsApp'a yapıştırın)", foreground="green").pack()

if __name__ == "__main__":
    App().mainloop()
