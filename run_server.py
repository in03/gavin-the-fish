from gavin_the_fish.server import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "gavin_the_fish.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable hot reloading
        reload_dirs=["src/gavin_the_fish"]  # Only watch the src directory
    ) 