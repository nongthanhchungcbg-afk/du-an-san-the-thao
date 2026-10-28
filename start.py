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

    try:
        from app.main import app
        print("-> FastAPI app imported successfully!")
        sys.stdout.flush()
    except Exception as e:
        print(f"-> ERROR IMPORTING APP: {e}")
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        sys.exit(1)

    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
