#!/usr/bin/env python3
"""
Clinic Management System - Main Run File
"""

import os
import sys
import subprocess

def check_dependencies():
    """Check installed requirements"""
    required = ['streamlit', 'pandas', 'plotly', 'openpyxl']
    missing = []

    for package in required:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            missing.append(package)
            print(f"❌ {package}")

    return missing

def main():
    print("=" * 50)
    print("🏥 Clinic Management System - Streamlit")
    print("=" * 50)

    print("🔍 Checking dependencies...")
    missing = check_dependencies()

    if missing:
        print(f"\n❌ Missing libraries: {missing}")
        print("Please install them using:")
        print("pip install " + " ".join(missing))
        input("\nPress Enter to close...")
        return

    print("\n✅ All requirements installed")
    print("🚀 Starting system...")

    # Run Streamlit
    try:
        subprocess.run(["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"])
    except KeyboardInterrupt:
        print("\n🛑 System stopped")
    except Exception as e:
        print(f"❌ Runtime error: {e}")

if __name__ == "__main__":
    main()