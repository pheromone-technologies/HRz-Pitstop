import os
import subprocess

categories = ["Tank bags", "Crash guards", "Lubricants/Oils"]

for cat in categories:
    print(f"\n\n========================================")
    print(f"Processing Category: {cat}")
    print(f"========================================")
    
    print(f"--- Running Pipeline Step 1-7 for {cat} ---")
    subprocess.run(["python", "scripts/pipeline.py", cat], check=True)
    
    print(f"--- Deleting category_mismatch for {cat} ---")
    subprocess.run(["python", "scripts/pipeline_stage2.py", "delete", "category_mismatch"], check=True)
    
    print(f"--- Compressing and Watermarking for {cat} ---")
    subprocess.run(["python", "scripts/pipeline_stage2.py", "compress"], check=True)
    
    print(f"--- Running Verification and Writing output for {cat} ---")
    subprocess.run(["python", "scripts/pipeline_stage2.py", "write", cat], check=True)
    
print("\nAll categories processed.")
