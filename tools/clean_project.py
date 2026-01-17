import os
import shutil

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

TARGETS = [
    "__pycache__",
    "reports",
    ".cache",
    ".tmp",
    ".temp",
    ".ipc",
]

EXTENSIONS = [
    ".pyc",
    ".pyo",
    ".log",
]

def remove_dir(path):
    if os.path.isdir(path):
        print(f"[DIR] removing {path}")
        shutil.rmtree(path, ignore_errors=True)

def remove_files(root):
    for dirpath, _, files in os.walk(root):
        for f in files:
            if f.endswith(tuple(EXTENSIONS)):
                full = os.path.join(dirpath, f)
                print(f"[FILE] removing {full}")
                os.remove(full)

def main():
    print("🧹 Cleaning project root:", BASE_DIR)

    for name in TARGETS:
        remove_dir(os.path.join(BASE_DIR, name))

    remove_files(BASE_DIR)

    print("✅ Clean complete")

if __name__ == "__main__":
    main()
