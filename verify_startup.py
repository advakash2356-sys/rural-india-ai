#!/usr/bin/env python3
"""
PRODUCTION STARTUP VERIFICATION SCRIPT
Validates all 6 phases before starting API server
"""

import sys
import asyncio
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_environment():
    """Verify Python environment"""
    print("\n" + "="*70)
    print("ENVIRONMENT VERIFICATION")
    print("="*70)
    
    # Check Python version
    py_version = sys.version_info
    if py_version.major < 3 or (py_version.major == 3 and py_version.minor < 9):
        print(f"❌ Python 3.9+ required. Found: {py_version.major}.{py_version.minor}")
        return False
    print(f"✅ Python {py_version.major}.{py_version.minor}.{py_version.micro}")
    
    # Check dependencies
    required_packages = [
        'fastapi', 'uvicorn', 'pydantic', 'requests', 'psutil',
        'paho', 'aiofiles', 'whisper', 'gtts', 'librosa',
        'numpy', 'scipy', 'sklearn'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} MISSING")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    return True

def check_directories():
    """Verify required directories"""
    print("\n" + "="*70)
    print("DIRECTORY VERIFICATION")
    print("="*70)
    
    required_dirs = [
        'edge_node',
        'data',
        'data/metrics',
        'data/backups',
        'logs',
        'models'
    ]
    
    all_ok = True
    for dirname in required_dirs:
        path = Path(dirname)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"📁 Created: {dirname}")
        else:
            print(f"✅ {dirname}/")
    
    return True

def check_modules():
    """Verify all system modules"""
    print("\n" + "="*70)
    print("MODULE VERIFICATION")
    print("="*70)
    
    modules = [
        ('edge_node.config.settings', 'Configuration'),
        ('edge_node.hardware.monitor', 'Hardware Monitor'),
        ('edge_node.hardware.power', 'Power Manager'),
        ('edge_node.models.manager', 'Model Manager'),
        ('edge_node.queue.async_queue', 'Request Queue'),
        ('edge_node.networking.mqtt_client', 'MQTT Client'),
        ('edge_node.core.orchestrator', 'Edge Orchestrator'),
        ('edge_node.voice.processor', 'Voice Processor'),
        ('edge_node.voice.speech_to_text', 'Speech-to-Text'),
        ('edge_node.voice.text_to_speech', 'Text-to-Speech'),
        ('edge_node.voice.audio_pipeline', 'Audio Pipeline'),
        ('edge_node.voice.service', 'Voice Service'),
        ('edge_node.rag.vector_db', 'Vector Database'),
        ('edge_node.agents.domain_agents', 'Domain Agents'),
        ('edge_node.safety.guardrails', 'Safety Guardrails'),
        ('edge_node.observability.monitor', 'Observability'),
    ]
    
    failed = []
    for module_name, display_name in modules:
        try:
            __import__(module_name)
            print(f"✅ {display_name}")
        except Exception as e:
            print(f"❌ {display_name}: {str(e)[:50]}")
            failed.append(display_name)
    
    if failed:
        print(f"\n⚠️  Failed modules: {', '.join(failed)}")
        return False
    
    return True

async def check_components():
    """Verify component initialization"""
    print("\n" + "="*70)
    print("COMPONENT INITIALIZATION")
    print("="*70)
    
    try:
        from edge_node.core.orchestrator import EdgeNodeOrchestrator
        
        print("Initializing orchestrator...")
        orchestrator = EdgeNodeOrchestrator()
        
        print("Starting edge node...")
        startup_ok = await orchestrator.startup()
        
        if startup_ok:
            print("✅ Edge Orchestrator")
        else:
            print("❌ Edge Orchestrator startup failed")
            return False
        
        # Check components
        if orchestrator.hardware_monitor:
            print("✅ Hardware Monitor")
        if orchestrator.power_manager:
            print("✅ Power Manager")
        if orchestrator.request_queue:
            print("✅ Request Queue")
        
        await orchestrator.shutdown()
        print("✅ Clean shutdown")
        
        return True
        
    except Exception as e:
        print(f"❌ Component check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all checks"""
    print("\n" + "╔" + "="*68 + "╗")
    print("║" + " "*15 + "PRODUCTION STARTUP VERIFICATION" + " "*21 + "║")
    print("╚" + "="*68 + "╝")
    
    checks = [
        ("Environment", check_environment()),
        ("Directories", check_directories()),
        ("Modules", check_modules()),
    ]
    
    # Run async check
    components_ok = await check_components()
    checks.append(("Components", components_ok))
    
    # Summary
    print("\n" + "="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)
    
    all_passed = all(result for _, result in checks)
    
    for check_name, result in checks:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name:20} {status}")
    
    print("="*70)
    
    if all_passed:
        print("\n🎉 ALL CHECKS PASSED - READY TO START API SERVER")
        print("\nRun: python3 api_server.py")
        return 0
    else:
        print("\n⚠️  SOME CHECKS FAILED - FIX ABOVE ISSUES FIRST")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
