"""Create a desktop shortcut for Jarvis4 AI Office with Iron Man icon."""
import os
import sys
import subprocess
from pathlib import Path


def create_shortcut():
    project_dir = Path(__file__).parent.resolve()
    icon_path = project_dir / "frontend" / "assets" / "jarvis.ico"
    launch_script = project_dir / "launch_office.py"
    python_exe = sys.executable

    desktop = Path(os.path.expanduser("~")) / "Desktop"
    shortcut_path = desktop / "Jarvis4 AI Office.lnk"

    try:
        ps_script = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{python_exe}"
$Shortcut.Arguments = '"{launch_script}"'
$Shortcut.WorkingDirectory = "{project_dir}"
$Shortcut.IconLocation = "{icon_path},0"
$Shortcut.Description = "Jarvis4 AI Office - Autonomous AI Organization"
$Shortcut.Save()
'''
        result = subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True, text=True
        )

        if result.returncode == 0:
            print(f"[OK] Shortcut created: {shortcut_path}")
            print(f"     Icon: {icon_path}")
            print(f"     Launch: {launch_script}")
        else:
            print(f"[ERROR] {result.stderr}")
            create_bat_shortcut(project_dir, desktop)

    except Exception as e:
        print(f"[ERROR] {e}")
        create_bat_shortcut(project_dir, desktop)


def create_bat_shortcut(project_dir, desktop):
    bat_path = desktop / "Jarvis4 AI Office.bat"
    python_exe = sys.executable
    launch_script = project_dir / "launch_office.py"

    with open(bat_path, 'w') as f:
        f.write(f'@echo off\n')
        f.write(f'title Jarvis4 AI Office\n')
        f.write(f'cd /d "{project_dir}"\n')
        f.write(f'"{python_exe}" "{launch_script}"\n')

    print(f"[OK] BAT file created: {bat_path}")


if __name__ == "__main__":
    create_shortcut()
