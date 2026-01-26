
import os
import re
from pypdf import PdfReader

# Configuration
SOURCE_FOLDER = "knowledge-base"
CLEAN_FOLDER = os.path.join(SOURCE_FOLDER, "cleaned")

# Ensure output folder exists
if not os.path.exists(CLEAN_FOLDER):
    os.makedirs(CLEAN_FOLDER)

def detect_mojibake_ratio(text):
    """
    Returns the ratio of 'suspicious' characters often found in 
    improperly decoded Indian legacy fonts.
    """
    if not text:
        return 0.0
    suspicious_chars = set("ÜO‚°‹§¬ôÝèv†ªêŠì‹ð˜£")
    count = sum(1 for c in text if c in suspicious_chars or (0xC0 <= ord(c) <= 0xFF))
    return count / len(text)

def clean_text(text):
    """
    Basic text cleaning:
    - Normalizes whitespace
    - Removes excessive newlines
    """
    # Replace multiple newlines with double newline
    text = re.sub(r'\n\s*\n', '\n\n', text)
    # Replace multiple spaces with single space
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

def process_file(filename):
    file_path = os.path.join(SOURCE_FOLDER, filename)
    target_path = os.path.join(CLEAN_FOLDER, f"{os.path.splitext(filename)[0]}.md")
    
    try:
        reader = PdfReader(file_path)
        full_text = ""
        
        # 1. Extract Text
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                full_text += extracted + "\n"
        
        # 2. Check Validty
        if not full_text.strip():
            return "skipped (empty)"
            
        ratio = detect_mojibake_ratio(full_text[:5000]) # Check first 5k chars
        
        # 3. Filter
        if ratio > 0.05: # Strict 5% threshold
            return f"skipped (corrupt: {ratio:.1%})"
            
        # 4. Clean & Save
        cleaned = clean_text(full_text)
        
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(f"# {filename}\n\n")
            f.write(cleaned)
            
        return "converted ✅"

    except Exception as e:
        return f"error ({str(e)})"

def main():
    print(f"🧹 Starting cleanup from '{SOURCE_FOLDER}' to '{CLEAN_FOLDER}'...\n")
    
    files = [f for f in os.listdir(SOURCE_FOLDER) if f.lower().endswith(".pdf")]
    
    for filename in files:
        result = process_file(filename)
        print(f"   • {filename}: {result}")
        
    print("\n✨ Cleanup complete. You can now run ingest_knowledge.py pointing to the 'cleaned' folder.")

if __name__ == "__main__":
    main()
