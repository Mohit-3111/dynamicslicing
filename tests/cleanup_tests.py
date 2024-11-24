from pathlib import Path

def cleanup():
    here = Path(__file__).parent
    # Remove the program-dynapyt.json files
    for file in here.rglob("program-dynapyt.json"):
        file.unlink()
    
    # Rename the program.py.orig files to program.py
    for file in here.rglob("program.py.orig"):
        file.rename(file.parent / "program.py")
    
    # Remove the sliced.py files
    for file in here.rglob("sliced.py"):
        file.unlink()

if __name__ == "__main__":
    cleanup()