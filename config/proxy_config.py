# Proxy Configuration
# Add your proxy servers here for IP rotation

# Example proxy configurations:
PROXY_SERVERS = [
    # HTTP Proxies
    # {"server": "http://proxy1.example.com:8080"},
    # {"server": "http://user:pass@proxy2.example.com:3128"},
    
    # SOCKS5 Proxies  
    # {"server": "socks5://proxy3.example.com:1080"},
    # {"server": "socks5://user:pass@proxy4.example.com:1080"},
    
    # Free proxy services (replace with working ones)
    # {"server": "http://free-proxy1.com:8080"},
    # {"server": "http://free-proxy2.com:3128"},
]

# Instructions:
# 1. Uncomment and modify the proxy entries above with real proxy servers
# 2. You can use free proxy services, VPN providers, or proxy services like:
#    - ProxyMesh, Bright Data, SmartProxy, etc.
# 3. Format: {"server": "protocol://[user:pass@]host:port"}
# 4. The scraper will randomly rotate between these proxies
# 5. Leave empty list [] to disable proxy rotation

# Security Note:
# - Use HTTPS proxies when possible
# - Avoid logging proxy credentials
# - Consider using residential proxies for better stealth
