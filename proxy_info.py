#!/usr/bin/env python3
"""
Proxy Information Tool
Shows available proxies and their status
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.shared.proxy_fetcher import proxy_fetcher
import json

def main():
    print("🌐 Fetching proxy information...")
    print("=" * 50)
    
    # Get proxy info
    info = proxy_fetcher.get_proxy_info()
    
    if isinstance(info, str):
        print(f"❌ {info}")
        return
    
    print(f"📊 Total Available Proxies: {info['total_proxies']}")
    print(f"🕒 Last Updated: {info['last_updated']}")
    print()
    
    print("🌍 Countries:")
    for country, count in sorted(info['countries'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {country}: {count} proxies")
    print()
    
    print("🔌 Protocols:")
    for protocol, count in info['protocols'].items():
        print(f"  {protocol.upper()}: {count} proxies")
    print()
    
    # Test getting a random proxy
    print("🎲 Testing random proxy selection...")
    proxy = proxy_fetcher.get_random_proxy()
    if proxy:
        print(f"✅ Selected: {proxy['server']}")
    else:
        print("❌ No proxy available")

if __name__ == "__main__":
    main()
