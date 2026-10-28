import os
import sys
import uvicorn

if __name__ == "__main__":
    port_str = os.environ.get("PORT", "10000")
    try:
        port = int(port_str)
    except Exception:
        port = 10000
    
    print(f"============================================================")
    print(f"  HE THONG QUAN LY SAN THE THAO KHOI DONG TAI PORT: {port}")
    print(f"============================================================")
    sys.stdout.flush()
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, log_level="info")
