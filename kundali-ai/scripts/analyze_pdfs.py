
import os
import sys
from pypdf import PdfReader

# Configuration
DATA_FOLDER = "knowledge-base"
REPORT_FILE = "knowledge_analysis_report.md"

def detect_mojibake_ratio(text):
    """
    Returns the ratio of 'suspicious' characters often found in 
    improperly decoded Indian legacy fonts (Latin-1 Supplement block).
    """
    if not text:
        return 0.0
        
    suspicious_chars = set("ÜO‚°‹§¬ôÝèv†ªêŠì‹ð˜£")
    count = sum(1 for c in text if c in suspicious_chars or (0xC0 <= ord(c) <= 0xFF))
    return count / len(text)

def analyze_pdfs():
    if not os.path.exists(DATA_FOLDER):
        print(f"Folder '{DATA_FOLDER}' not found.")
        return

    files = [f for f in os.listdir(DATA_FOLDER) if f.lower().endswith(".pdf")]
    
    report_lines = ["# 📊 Knowledge Base PDF Analysis Report\n", "| Filename | Pages Analyzed | Status | Garbage Ratio | Preview |\n|---|---|---|---|---|"]
    
    print(f"🔍 Analyzing {len(files)} PDFs in '{DATA_FOLDER}'...\n")

    for filename in files:
        file_path = os.path.join(DATA_FOLDER, filename)
        status = "✅ Valid"
        preview = ""
        ratio = 0.0
        
        try:
            reader = PdfReader(file_path)
            # Analyze just the first page or first 1000 chars
            check_text = ""
            if len(reader.pages) > 0:
                check_text = reader.pages[0].extract_text()
            
            if not check_text:
                status = "⚠️ Empty/Scanned"
            else:
                ratio = detect_mojibake_ratio(check_text)
                preview = check_text[:50].replace("\n", " ")
                
                if ratio > 0.2:
                    status = "❌ CORRUPT (Mojibake)"
                elif ratio > 0.05:
                    status = "⚠️ Suspicious"
                    
        except Exception as e:
            status = f"❌ Error: {str(e)}"

        # Console Output
        print(f"   • {filename}: {status} ({ratio:.1%})")
        
        # Report Output
        row = f"| {filename} | {len(reader.pages) if 'reader' in locals() else 'N/A'} | {status} | {ratio:.1%} | `{preview}`... |"
        report_lines.append(row)

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
        
    print(f"\n📄 Report saved to: {REPORT_FILE}")

if __name__ == "__main__":
    analyze_pdfs()
