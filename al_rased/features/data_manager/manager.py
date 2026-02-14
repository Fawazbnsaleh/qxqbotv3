import json
import logging
from pathlib import Path

DATA_DIR = Path("data")
SAMPLES_FILE = DATA_DIR / "samples4Review/data.json"

def get_review_data():
    if not SAMPLES_FILE.exists():
        return None
    try:
        with open(SAMPLES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error reading review data: {e}")
        return None

RESULTS_DIR = DATA_DIR / "results"

def save_model_results(model_version: str, results: list):
    """
    Saves model evaluation results to a JSON file named after the model version.
    
    Args:
        model_version (str): The version of the model (e.g., 'v1.0').
        results (list): A list of dictionaries containing the evaluation results.
    """
    if not RESULTS_DIR.exists():
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        
    file_path = RESULTS_DIR / f"{model_version}.json"
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logging.info(f"Saved results for model {model_version} to {file_path}")
        return True
    except Exception as e:
        logging.error(f"Error saving model results: {e}")
        return False
