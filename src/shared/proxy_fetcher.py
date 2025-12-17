import requests
import random
import time
from src.shared.log import logger

class ProxyFetcher:
    def __init__(self):
        self.proxy_cache = []
        self.last_fetch = 0
        self.cache_duration = 1800  # 30 minutes cache
        self.api_url = "https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc"
    
    def _fetch_fresh_proxies(self):
        """
        Fetch fresh proxy list from the API
        """
        try:
            logger.info("Fetching fresh proxy list from geonode.com...")
            response = requests.get(self.api_url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            proxies = data.get('data', [])
            
            # Filter and format proxies
            valid_proxies = []
            for proxy in proxies:
                # Only use proxies with good uptime (>80%) and recent check
                uptime = proxy.get('upTime', 0)
                protocols = proxy.get('protocols', [])
                
                if uptime > 80 and protocols:
                    ip = proxy.get('ip')
                    port = proxy.get('port')
                    country = proxy.get('country', 'Unknown')
                    city = proxy.get('city', 'Unknown')
                    
                    # Prefer HTTP for better compatibility, avoid SOCKS4
                    if 'http' in protocols:
                        protocol = 'http'
                    elif 'socks5' in protocols:
                        protocol = 'socks5'
                    else:
                        continue  # Skip SOCKS4 as it's less reliable
                    
                    proxy_entry = {
                        "server": f"{protocol}://{ip}:{port}",
                        "ip": ip,
                        "port": port,
                        "country": country,
                        "city": city,
                        "uptime": uptime,
                        "protocol": protocol
                    }
                    valid_proxies.append(proxy_entry)
            
            logger.info(f"Fetched {len(valid_proxies)} valid proxies from {len(proxies)} total")
            
            # Sort by uptime (best first)
            valid_proxies.sort(key=lambda x: x['uptime'], reverse=True)
            
            self.proxy_cache = valid_proxies
            self.last_fetch = time.time()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to fetch proxies from API: {e}")
            return False
    
    def get_random_proxy(self):
        """
        Get a random proxy from the cache, refresh if needed
        """
        current_time = time.time()
        
        # Refresh cache if expired or empty
        if (current_time - self.last_fetch > self.cache_duration) or not self.proxy_cache:
            if not self._fetch_fresh_proxies():
                logger.warning("Could not fetch fresh proxies, using cached ones if available")
        
        if not self.proxy_cache:
            logger.warning("No proxies available")
            return None
        
        # Get random proxy from top 50% (best uptimes)
        top_proxies = self.proxy_cache[:len(self.proxy_cache)//2] if len(self.proxy_cache) > 10 else self.proxy_cache
        proxy = random.choice(top_proxies)
        
        logger.debug(f"Selected proxy: {proxy['ip']}:{proxy['port']} ({proxy['country']}/{proxy['city']}) - {proxy['uptime']:.1f}% uptime")
        
        return {"server": proxy["server"]}
    
    def get_proxy_info(self):
        """
        Get information about available proxies
        """
        if not self.proxy_cache:
            self._fetch_fresh_proxies()
        
        if not self.proxy_cache:
            return "No proxies available"
        
        countries = {}
        protocols = {}
        
        for proxy in self.proxy_cache:
            country = proxy['country']
            protocol = proxy['protocol']
            
            countries[country] = countries.get(country, 0) + 1
            protocols[protocol] = protocols.get(protocol, 0) + 1
        
        return {
            "total_proxies": len(self.proxy_cache),
            "countries": countries,
            "protocols": protocols,
            "last_updated": time.ctime(self.last_fetch)
        }

# Global proxy fetcher instance
proxy_fetcher = ProxyFetcher()
