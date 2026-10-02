import os
import subprocess
from datetime import datetime

# المجلد اللي هيتخزن فيه التقارير
REPORT_DIR = "security_reports"

# الأوامر اللي هنفحص بيها
COMMANDS = {
    "bandit": ["bandit", "-r", ".", "-f", "html", "-o", f"{REPORT_DIR}/bandit-report.html"],
    "pip-audit": ["pip-audit", "-r", "requirements.txt", "-f", "html", "-o", f"{REPORT_DIR}/pip-audit.html"],
    "safety": ["safety", "check", "-r", "requirements.txt", "--full-report"],
    "semgrep": ["semgrep", "scan", "--config", "p/ci", "--json", "-o", f"{REPORT_DIR}/semgrep-report.json"],
}

def run_command(name, cmd):
    print(f"\n🚀 Running {name}...")
    try:
        if name == "safety":  # safety بيطبع في stdout
            result = subprocess.run(cmd, capture_output=True, text=True)
            with open(f"{REPORT_DIR}/safety-report.txt", "w", encoding="utf-8") as f:
                f.write(result.stdout)
        else:
            subprocess.run(cmd, check=False)
        print(f"✅ {name} done.")
    except Exception as e:
        print(f"❌ Error running {name}: {e}")

def main():
    # أنشئ مجلد للتقارير
    os.makedirs(REPORT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"🔍 Starting security checks at {timestamp}")

    for name, cmd in COMMANDS.items():
        run_command(name, cmd)

    print("\n🎉 All checks finished!")
    print(f"📂 Reports saved in: {os.path.abspath(REPORT_DIR)}")

if __name__ == "__main__":
    main()
