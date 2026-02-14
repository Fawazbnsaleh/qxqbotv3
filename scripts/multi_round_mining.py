"""
Multi-Round Mining Loop.
Runs multiple iterations of mining + training + calibration.
"""
import subprocess
import sys

ROUNDS = 3

for i in range(ROUNDS):
    print(f"\n{'='*60}")
    print(f"=== ROUND {i+1}/{ROUNDS} ===")
    print(f"{'='*60}\n")
    
    # 1. Deep Mining
    print("Step 1: Deep Mining...")
    result = subprocess.run([
        sys.executable, "scripts/deep_mining.py"
    ], cwd="/Users/apple/qxqbotv3")
    
    # 2. Targeted Mining
    print("\nStep 2: Targeted Mining...")
    result = subprocess.run([
        sys.executable, "scripts/targeted_mining.py"
    ], cwd="/Users/apple/qxqbotv3")
    
    # 3. Training
    print("\nStep 3: Training...")
    result = subprocess.run([
        sys.executable, "-u", "al_rased/features/model/train.py"
    ], cwd="/Users/apple/qxqbotv3")
    
    # 4. Calibration
    print("\nStep 4: Calibrating Thresholds...")
    result = subprocess.run([
        sys.executable, "scripts/calibrate_thresholds.py"
    ], cwd="/Users/apple/qxqbotv3")

print(f"\n{'='*60}")
print("=== ALL ROUNDS COMPLETE ===")
print(f"{'='*60}\n")

# Final simulation
print("Running Final Simulation...")
result = subprocess.run([
    sys.executable, "scripts/simulate_with_score.py"
], cwd="/Users/apple/qxqbotv3")
