"""
UYTCAB Pipeline Orchestrator
Automated pipeline to download and process daily signal PDFs

Flow:
1. Run main.py - Download latest PDF from uedayagi.com
2. Run map.py - Extract and map fiscal forecast data to CSV
"""

import subprocess
import sys
import os
from datetime import datetime

def run_script(script_name, description):
    """
    Run a Python script and handle errors

    Args:
        script_name: Name of the script to run
        description: Description of what the script does

    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\n{'='*60}")
    print(f"[*] {description}")
    print(f"[*] Running: {script_name}")
    print(f"{'='*60}\n")

    try:
        # Run the script
        result = subprocess.run(
            [sys.executable, script_name],
            check=True,
            capture_output=False,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        print(f"\n[+] {script_name} completed successfully!")
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n[!] Error running {script_name}")
        print(f"[!] Exit code: {e.returncode}")
        return False
    except Exception as e:
        print(f"\n[!] Unexpected error running {script_name}: {str(e)}")
        return False

def main():
    """Main orchestrator function"""
    start_time = datetime.now()

    print("="*60)
    print("UYTCAB PIPELINE ORCHESTRATOR")
    print("="*60)
    print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Step 1: Download PDF
    success = run_script("main.py", "Step 1: Download latest PDF report")
    if not success:
        print("\n[!] Pipeline failed at Step 1 (PDF download)")
        sys.exit(1)

    # Step 2: Process and map PDF data
    success = run_script("map.py", "Step 2: Extract and map fiscal forecast data")
    if not success:
        print("\n[!] Pipeline failed at Step 2 (Data mapping)")
        sys.exit(1)

    # Pipeline completed
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print("\n" + "="*60)
    print("[+] PIPELINE COMPLETED SUCCESSFULLY!")
    print("="*60)
    print(f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total duration: {duration:.2f} seconds")
    print("\n[*] Output file: output_mapped_data.csv")
    print("="*60)

if __name__ == "__main__":
    main()
