#!/usr/bin/env python3
"""
AlitaOS Voice Feature Test Script
Tests voice/audio functionality and browser compatibility
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*50}")
    print(f"🎙️  {title}")
    print(f"{'='*50}")

def print_success(message):
    """Print success message"""
    print(f"✅ {message}")

def print_error(message):
    """Print error message"""
    print(f"❌ {message}")

def print_warning(message):
    """Print warning message"""
    print(f"⚠️  {message}")

def print_info(message):
    """Print info message"""
    print(f"ℹ️  {message}")

def check_ssl_certificates():
    """Check if SSL certificates exist for HTTPS"""
    print_header("SSL Certificate Check")
    
    cert_file = Path("cert.pem")
    key_file = Path("key.pem")
    
    if cert_file.exists() and key_file.exists():
        print_success("SSL certificates found")
        return True
    else:
        print_warning("SSL certificates not found")
        print_info("Run ./launch_https.sh to generate certificates automatically")
        return False

def check_openssl():
    """Check if OpenSSL is available for certificate generation"""
    print_header("OpenSSL Availability Check")
    
    try:
        result = subprocess.run(['openssl', 'version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print_success(f"OpenSSL found: {result.stdout.strip()}")
            return True
        else:
            print_error("OpenSSL not working properly")
            return False
    except FileNotFoundError:
        print_error("OpenSSL not found")
        print_info("Install OpenSSL to enable HTTPS support for voice features")
        return False
    except subprocess.TimeoutExpired:
        print_error("OpenSSL command timed out")
        return False

def check_browser_compatibility():
    """Provide browser compatibility information"""
    print_header("Browser Compatibility Guide")
    
    print_info("Voice features work best with:")
    print("  🌐 Chrome (recommended)")
    print("  🦊 Firefox")
    print("  🧭 Safari")
    print("  🚫 Avoid Internet Explorer/Edge Legacy")
    
    print_info("Requirements:")
    print("  🔒 HTTPS connection (use ./launch_https.sh)")
    print("  🎤 Microphone permissions granted")
    print("  🔊 Audio output enabled")

def test_microphone_access_script():
    """Generate a JavaScript test for microphone access"""
    print_header("Microphone Access Test")
    
    js_test = """
// Paste this into your browser's console to test microphone access
navigator.mediaDevices.getUserMedia({ audio: true })
  .then(stream => {
    console.log('✅ Microphone access granted');
    console.log('Audio tracks:', stream.getAudioTracks().length);
    stream.getTracks().forEach(track => {
      console.log('Track:', track.label, 'State:', track.readyState);
      track.stop();
    });
  })
  .catch(err => {
    console.error('❌ Microphone access denied:', err.name, err.message);
    if (err.name === 'NotAllowedError') {
      console.log('💡 Solution: Grant microphone permissions in browser settings');
    } else if (err.name === 'NotFoundError') {
      console.log('💡 Solution: Check if microphone is connected and working');
    } else if (err.name === 'NotSupportedError') {
      console.log('💡 Solution: Use HTTPS or try a different browser');
    }
  });
"""
    
    print_info("Copy and paste this JavaScript into your browser console:")
    print(f"```javascript{js_test}```")

def check_environment():
    """Check environment setup"""
    print_header("Environment Check")
    
    # Check .env file
    env_file = Path(".env")
    if env_file.exists():
        print_success(".env file found")
        
        # Check for OpenAI API key
        with open(env_file, 'r') as f:
            content = f.read()
            if 'OPENAI_API_KEY' in content:
                print_success("OPENAI_API_KEY found in .env")
            else:
                print_error("OPENAI_API_KEY not found in .env")
                return False
    else:
        print_error(".env file not found")
        print_info("Create .env file with OPENAI_API_KEY=your_key_here")
        return False
    
    # Check virtual environment
    venv_path = Path(".venv")
    if venv_path.exists():
        print_success("Virtual environment found")
    else:
        print_warning("Virtual environment not found")
        print_info("Run ./launch.sh or ./launch_https.sh to create it")
    
    return True

def provide_troubleshooting_steps():
    """Provide step-by-step troubleshooting"""
    print_header("Voice Feature Troubleshooting Steps")
    
    steps = [
        "1. 🔒 Use HTTPS launch: ./launch_https.sh",
        "2. 🌐 Open https://localhost:8000 in Chrome",
        "3. 🔓 Accept security warning (click Advanced → Proceed)",
        "4. 🎤 Grant microphone permissions when prompted",
        "5. 🔊 Check system audio/microphone settings",
        "6. 🧹 Clear browser cache (Ctrl+Shift+R)",
        "7. 🔄 Try incognito/private browsing mode",
        "8. 📱 Test on different device if issues persist"
    ]
    
    for step in steps:
        print(f"   {step}")

def main():
    """Main test function"""
    print_header("AlitaOS Voice Feature Test")
    print("This script helps diagnose voice/audio issues")
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    all_checks_passed = True
    
    # Run checks
    if not check_environment():
        all_checks_passed = False
    
    check_openssl()
    check_ssl_certificates()
    check_browser_compatibility()
    test_microphone_access_script()
    provide_troubleshooting_steps()
    
    # Final recommendations
    print_header("Recommendations")
    
    if all_checks_passed:
        print_success("Environment looks good!")
        print_info("To test voice features:")
        print("  1. Run: ./launch_https.sh")
        print("  2. Open: https://localhost:8000")
        print("  3. Grant microphone permissions")
        print("  4. Click the microphone button to start voice chat")
    else:
        print_warning("Some issues found - see above for solutions")
    
    print_info("For detailed troubleshooting: AUDIO_TROUBLESHOOTING.md")
    print_info("If issues persist, try text-only mode first")

if __name__ == "__main__":
    main()
