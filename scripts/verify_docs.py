import os
import re

def verify_docs():
    index_path = os.path.join("docs", "index.html")
    assert os.path.exists(index_path), "docs/index.html does not exist"
    
    with open(index_path, "r", encoding="utf-8") as f:
        html = f.read()
        
    srcs = re.findall(r'(?:src|href)=["\']([^"\'#:]+)["\']', html)
    missing = []
    checked = []
    for s in srcs:
        if any(s.endswith(ext) for ext in [".css", ".js", ".png", ".jpg", ".svg", ".html"]):
            if not s.startswith("http"):
                target = os.path.normpath(os.path.join("docs", s))
                checked.append((s, target))
                if not os.path.exists(target):
                    missing.append((s, target))
                    
    print(f"Checked {len(checked)} assets:")
    for s, target in checked:
        print(f"  [OK] {s} -> {target}")
        
    if missing:
        print("Missing assets:", missing)
        return False
        
    print("ALL STATIC ASSETS VERIFIED SUCCESSFULLY!")
    return True

if __name__ == "__main__":
    success = verify_docs()
    exit(0 if success else 1)
