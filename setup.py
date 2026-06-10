import os
import subprocess
import sys

def run_command(command_list):
    """Helper function to run system commands safely."""
    try:
        subprocess.run(command_list, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error executing: {' '.join(command_list)}")
        sys.exit(1)

def main():
    print("\n🚀 Starting Universal FitnessHub Setup Wrapper...")

    # NEW SAFETY MEASURE: Delete existing clean db if starting over to avoid collisions
    if os.path.exists("db.sqlite3"):
        print("🧹 Clearing preexisting db.sqlite3 file to guarantee clean metadata table installation...")
        try:
            os.remove("db.sqlite3")
        except Exception as e:
            print(f"⚠️ Warning: Could not auto-delete db.sqlite3: {e}")

    # 1. Install dependencies from freeze list
    print("\n📦 Step 1: Installing Python dependencies from requirements.txt...")
    run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

    # 2. Build database structure cleanly
    print("\n🔄 Step 2: Generating clean database tables (migrations)...")
    run_command([sys.executable, "manage.py", "migrate"])

    # 3. Load master seed files smoothly
    print("\n📥 Step 3: Injecting baseline data states...")
    seed_files = ["store.json", "users_data.json", "store_data.json", "master_seed.json"]
    for file in seed_files:
        if os.path.exists(file):
            print(f"   -> Loading fixture: {file}")
            run_command([sys.executable, "manage.py", "loaddata", file])

    # 4. Automatically run image re-linker
    if os.path.exists("relink.py"):
        print("\n🔗 Step 4: Re-linking media product and category assets...")
        run_command([sys.executable, "relink.py"])

    print("\n🎉 Everything is fully configured and linked without conflicts!")
    print("👉 To start your application, run: python manage.py runserver 9000\n")

if __name__ == "__main__":
    main()