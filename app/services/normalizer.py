import re
import json
import logging
from pathlib import Path
from typing import Dict
from app.core.config import settings

logger = logging.getLogger(__name__)

class CompanyNormalizer:
    """
    Standardizes company names using a local dictionary (shortnames.json).
    Prevents AI hallucination and reduces token usage.
    """
    
    def __init__(self, dictionary_path: Path | None = None):
        # Default to a file in the data directory if not provided
        self.dict_path = dictionary_path or settings.DATA_DIR / "shortnames.json"
        self.mappings: Dict[str, str] = self._load_dictionary()

    def _load_dictionary(self) -> Dict[str, str]:
        """Loads the shortname mapping from a JSON file."""
        if not self.dict_path.exists():
            logger.warning(f"Shortnames dictionary not found at {self.dict_path}. Creating empty one.")
            # Initialize with an empty dictionary if file doesn't exist
            self._save_dictionary({})
            return {}
        
        try:
            with open(self.dict_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading shortnames dictionary: {e}")
            return {}

    def _save_dictionary(self, data: Dict[str, str]):
        """Persists the dictionary to disk."""
        try:
            with open(self.dict_path, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving shortnames dictionary: {e}")

    def normalize(self, raw_name: str) -> str:
        """
        Takes a raw name (e.g., 'The Home Depot Inc.') and returns 
        the standardized version (e.g., 'HomeDepot').
        """
        if not raw_name:
            return "Unknown_Company"

        # 1. Basic Cleanup: Remove common suffixes and special characters
        clean_name = raw_name.strip()
        # Remove common business suffixes (case insensitive)
        clean_name = re.sub(r'\b(inc|corp|llc|ltd|incorporated|corporation)\b\.?', '', clean_name, flags=re.IGNORECASE)
        # Remove non-alphanumeric characters but keep spaces for matching
        clean_name = re.sub(r'[^\w\s]', '', clean_name).strip()
        
        # 2. Check Dictionary Match
        # We check against keys converted to lowercase for better matching
        search_name = clean_name.lower()
        for key, standardized in self.mappings.items():
            if key.lower() == search_name:
                return standardized
        
        # 3. Fallback: If no match found, create a safe filename version
        # Remove all spaces for the final filename
        return clean_name.replace(" ", "")

    def add_mapping(self, raw_name: str, standardized_name: str):
        """Allows programmatically adding new mappings to the local dictionary."""
        self.mappings[raw_name] = standardized_name
        self._save_dictionary(self.mappings)
        logger.info(f"Added new mapping: {raw_name} -> {standardized_name}")