import json
import pandas as pd
import numpy as np
from typing import List, Dict, Any
import logging
from app.services.storage_service import storage_service

logger = logging.getLogger(__name__)

class ProcessingService:
    def __init__(self):
        pass

    def flatten_data(self, data: List[Dict[str, Any]], preserve_nested: bool = True) -> List[Dict[str, Any]]:
        """
        Processes raw Apify data for better usability while preserving structure.
        
        Args:
            data: Raw data from Apify
            preserve_nested: If True, keeps nested structures as JSON strings instead of flattening
        
        Returns:
            Processed data with optional flattening
        """
        try:
            if not data:
                return []
            
            if preserve_nested:
                # Keep nested structures intact but ensure JSON serializable
                processed_data = []
                for item in data:
                    processed_item = {}
                    for key, value in item.items():
                        # Keep complex types as-is for JSON serialization
                        processed_item[key] = value
                    processed_data.append(processed_item)
                logger.info("Data processed while preserving nested structures")
                return processed_data
            else:
                # Original flattening logic for backwards compatibility
                df = pd.json_normalize(data)
                
                for col in df.columns:
                    if df[col].apply(lambda x: isinstance(x, list)).any():
                        df[col] = df[col].apply(
                            lambda x: ", ".join([str(i) for i in x]) if isinstance(x, list) else x
                        )
                
                df = df.replace({np.nan: None})
                flattened_data = df.to_dict(orient="records")
                logger.info("Data flattened into tabular format")
                return flattened_data
            
        except Exception as e:
            logger.error(f"Error processing data: {str(e)}")
            raise e

    def process_and_save_data(self, platform: str, raw_filepath: str) -> str:
        """
        Loads raw JSON data from filepath, flattens it, and saves it to the processed directory.
        """
        try:
            with open(raw_filepath, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
                
            flattened_data = self.flatten_data(raw_data)
            
            processed_filepath = storage_service.save_processed_data(platform, flattened_data)
            logger.info(f"Successfully processed and saved {platform} data to {processed_filepath}")
            return processed_filepath
        except Exception as e:
            logger.error(f"Error in process_and_save_data for {platform}: {str(e)}")
            raise e

processing_service = ProcessingService()
