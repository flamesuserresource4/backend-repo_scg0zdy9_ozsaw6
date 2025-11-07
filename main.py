import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Any, Dict
import importlib
import inspect
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        # Try to import database module
        from database import db
        
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            # Try to list collections to verify connectivity
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response

@app.get("/schema")
def get_schema() -> Dict[str, Any]:
    """Return Pydantic schemas defined in schemas.py so the UI can fast-generate collections.
    Each class is mapped to a collection using its lowercase class name.
    """
    try:
        schemas_module = importlib.import_module("schemas")
    except Exception as e:
        return {"error": f"Unable to import schemas: {str(e)}"}

    definitions: Dict[str, Any] = {}

    for name, obj in inspect.getmembers(schemas_module):
        if inspect.isclass(obj) and issubclass(obj, BaseModel) and obj.__module__ == schemas_module.__name__:
            model = obj
            fields_info = []
            for fname, f in model.model_fields.items():  # pydantic v2
                field_type = str(f.annotation)
                required = f.is_required()
                default = None if required else (f.default if f.default is not None else None)
                description = None
                if getattr(f, 'description', None):
                    description = f.description
                fields_info.append({
                    "name": fname,
                    "type": field_type,
                    "required": required,
                    "default": default,
                    "description": description,
                })

            definitions[name] = {
                "collection": name.lower(),
                "title": name,
                "fields": fields_info,
            }
    
    return {"schemas": definitions}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
