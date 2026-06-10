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

    # 1. Update pip and install dependencies from your freeze list
    print("\n📦 Step 1: Installing Python dependencies from requirements.txt...")
    run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

    # 2. Build the database structure
    print("\n🔄 Step 2: Generating local database tables (migrations)...")
    run_command([sys.executable, "manage.py", "migrate"])

    # 3. Load data files in the correct safe order
    print("\n📥 Step 3: Injecting baseline data states...")
    seed_files = ["store.json", "users_data.json", "store_data.json", "master_seed.json"]
    for file in seed_files:
        if os.path.exists(file):
            print(f"   -> Loading fixture: {file}")
            run_command([sys.executable, "manage.py", "loaddata", file])

    # 4. Automatically run the image re-linker
    if os.path.exists("relink.py"):
        print("\n🔗 Step 4: Re-linking media product and category assets...")
        run_command([sys.executable, "relink.py"])

    print("\n🎉 Everything is fully configured and linked!")
    print("👉 To start your application, run: python manage.py runserver 9000\n")

if __name__ == "__main__":
    main()