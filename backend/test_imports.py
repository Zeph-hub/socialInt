import sys
import os

# Add the current directory to sys.path so 'app' can be found
sys.path.append(os.getcwd())

try:
    from app.main import app
    from app.ingestion.factory import ingestion_factory
    from app.services.normalization_service import normalization_service
    
    print("Success: Backend app and modular services initialized correctly.")
    print(f"Registered platforms: {list(ingestion_factory._services.keys())}")
except Exception as e:
    print(f"Error: Failed to initialize. {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
