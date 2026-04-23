#!/usr/bin/env python3
import uvicorn
from config import WEB_ADMIN_HOST, WEB_ADMIN_PORT

if __name__ == "__main__":
    uvicorn.run(
        "web_admin.app:app",
        host=WEB_ADMIN_HOST,
        port=WEB_ADMIN_PORT,
        reload=True
    )