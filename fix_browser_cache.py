#!/usr/bin/env python3
"""
Browser Cache Fix Script for AlitaOS Voice Issues
Helps resolve MIME type and media access errors
"""

import os
import subprocess
import sys
from pathlib import Path

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🔧 {title}")
    print(f"{'='*60}")

def print_step(step, description):
    print(f"\n{step}. {description}")

def print_success(message):
    print(f"   ✅ {message}")

def print_info(message):
    print(f"   ℹ️  {message}")

def print_warning(message):
    print(f"   ⚠️  {message}")

def clear_browser_caches():
    """Provide instructions for clearing browser caches"""
    print_header("Browser Cache Clearing Instructions")
    
    print_step("1", "Chrome Cache Clearing")
    print_info("Press: Cmd+Shift+Delete (Mac) or Ctrl+Shift+Delete (Windows)")
    print_info("Or go to: Chrome → Settings → Privacy and Security → Clear browsing data")
    print_info("Select: 'Cached images and files' and 'Cookies and other site data'")
    print_info("Time range: 'All time'")
    
    print_step("2", "Firefox Cache Clearing")
    print_info("Press: Cmd+Shift+Delete (Mac) or Ctrl+Shift+Delete (Windows)")
    print_info("Or go to: Firefox → Preferences → Privacy & Security → Clear Data")
    print_info("Check: 'Cached Web Content' and 'Cookies and Site Data'")
    
    print_step("3", "Safari Cache Clearing")
    print_info("Press: Cmd+Option+E (Mac)")
    print_info("Or go to: Safari → Preferences → Privacy → Manage Website Data → Remove All")

def reset_browser_permissions():
    """Instructions for resetting browser permissions"""
    print_header("Browser Permission Reset")
    
    print_step("1", "Chrome Permission Reset")
    print_info("Go to: chrome://settings/content/microphone")
    print_info("Find localhost:8000 in the list and remove it")
    print_info("Or click the lock icon in address bar → Reset permissions")
    
    print_step("2", "Firefox Permission Reset")
    print_info("Go to: about:preferences#privacy")
    print_info("Scroll to 'Permissions' → Click 'Settings' next to Microphone")
    print_info("Find localhost and remove it")
    
    print_step("3", "Safari Permission Reset")
    print_info("Go to: Safari → Preferences → Websites → Microphone")
    print_info("Find localhost and change to 'Ask' or remove it")

def create_chainlit_config():
    """Create a Chainlit config to potentially fix MIME issues"""
    print_header("Creating Chainlit Configuration")
    
    config_content = """[project]
# Chainlit configuration for AlitaOS
enable_telemetry = false

[UI]
name = "AlitaOS"
description = "Your streamlined AI assistant powered by OpenAI"
default_collapse_content = true
default_expand_messages = false
hide_cot = false
show_readme_as_default = true

[meta]
generated_by = "1.0.0"
"""
    
    config_path = Path("app/.chainlit/config.toml")
    config_path.parent.mkdir(exist_ok=True)
    
    try:
        with open(config_path, 'w') as f:
            f.write(config_content)
        print_success(f"Created Chainlit config: {config_path}")
        return True
    except Exception as e:
        print_warning(f"Could not create config: {e}")
        return False

def check_microphone_system():
    """Check system microphone availability"""
    print_header("System Microphone Check")
    
    try:
        # Check if system_profiler is available (macOS)
        result = subprocess.run(['system_profiler', 'SPAudioDataType'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            if 'Built-in Microphone' in result.stdout or 'Microphone' in result.stdout:
                print_success("System microphone detected")
            else:
                print_warning("No microphone found in system audio devices")
        else:
            print_info("Could not check system audio devices")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print_info("System audio check not available on this platform")

def provide_manual_test():
    """Provide manual browser test"""
    print_header("Manual Browser Test")
    
    print_step("1", "Open Browser Developer Tools")
    print_info("Press F12 or right-click → Inspect")
    print_info("Go to Console tab")
    
    print_step("2", "Test Microphone Access")
    print_info("Paste this code and press Enter:")
    print("""
navigator.mediaDevices.getUserMedia({ 
    audio: { 
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
        sampleRate: 24000
    } 
})
.then(stream => {
    console.log('✅ SUCCESS: Microphone access granted');
    console.log('Audio tracks:', stream.getAudioTracks().length);
    stream.getAudioTracks().forEach(track => {
        console.log('Track settings:', track.getSettings());
        track.stop();
    });
})
.catch(err => {
    console.error('❌ FAILED:', err.name, '-', err.message);
    console.log('Constraint error:', err.constraint);
});
""")

def main():
    print_header("AlitaOS Browser Cache & Permission Fix")
    print("This script helps resolve MIME type and microphone access errors")
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Run fixes
    clear_browser_caches()
    reset_browser_permissions()
    create_chainlit_config()
    check_microphone_system()
    provide_manual_test()
    
    print_header("Next Steps")
    print_step("1", "Clear your browser cache using the instructions above")
    print_step("2", "Reset browser permissions for localhost")
    print_step("3", "Restart your browser completely")
    print_step("4", "Try the HTTPS launch: ./launch_https.sh")
    print_step("5", "Open https://localhost:8000 and test microphone")
    print_step("6", "If still having issues, try the manual browser test above")
    
    print_info("The Chainlit config has been created to potentially resolve MIME issues")
    print_info("If problems persist, the issue may be with Chainlit's audio handling")

if __name__ == "__main__":
    main()
