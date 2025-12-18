# Production Deployment Guide

## Scenario 1: API on Hostinger + PWA on Domain

### ✅ Yes, it will work! Here's what you need:

#### 1. **API Server Setup (Hostinger)**

**Requirements:**
- Python 3.8+ support
- Ability to run long-running processes (background worker)
- SQLite database storage

**Steps:**

1. **Upload files to Hostinger:**
   ```bash
   # Upload all files except test-pwa/ to your Hostinger server
   # Structure:
   /home/username/avto-net-scrapper/
   ├── api_server.py
   ├── src/
   ├── requirements/
   ├── data/          # Will be created automatically
   └── logs/          # Will be created automatically
   ```

2. **Install dependencies:**
   ```bash
   ssh your-hostinger-server
   cd ~/avto-net-scrapper
   pip3 install -r requirements/common.txt
   playwright install chromium
   ```

3. **Set environment variables:**
   ```bash
   # Create .env file or set in Hostinger control panel
   export DB_PATH=/home/username/avto-net-scrapper/data/scraper.db
   export PORT=8000
   export CORS_ORIGINS=https://your-pwa-domain.com,https://www.your-pwa-domain.com
   export SCRAPE_INTERVAL=60
   ```

4. **Run as a service (using systemd or PM2):**
   
   **Option A: systemd (Linux)**
   ```bash
   # Create /etc/systemd/system/avto-scraper.service
   [Unit]
   Description=Avto-Net Scraper API
   After=network.target

   [Service]
   Type=simple
   User=username
   WorkingDirectory=/home/username/avto-net-scrapper
   Environment="PATH=/usr/bin:/usr/local/bin"
   Environment="DB_PATH=/home/username/avto-net-scrapper/data/scraper.db"
   Environment="CORS_ORIGINS=https://your-pwa-domain.com"
   ExecStart=/usr/bin/python3 /home/username/avto-net-scrapper/api_server.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
   
   ```bash
   sudo systemctl enable avto-scraper
   sudo systemctl start avto-scraper
   ```

   **Option B: PM2 (Node.js process manager)**
   ```bash
   npm install -g pm2
   pm2 start api_server.py --name avto-scraper --interpreter python3
   pm2 save
   pm2 startup
   ```

5. **Configure reverse proxy (nginx/Apache):**
   
   **Nginx example:**
   ```nginx
   server {
       listen 80;
       server_name api.your-domain.com;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

#### 2. **PWA Setup (Your Domain)**

1. **Upload PWA files:**
   ```bash
   # Upload test-pwa/ contents to your domain's public_html/
   # Structure:
   /public_html/
   ├── index.html
   ├── manifest.json
   └── (other assets)
   ```

2. **Update API URL in PWA:**
   
   **Option A: Hardcode in HTML:**
   ```javascript
   // In test-pwa/index.html, change:
   let API_BASE_URL = 'https://api.your-domain.com';  // Your Hostinger API URL
   ```

   **Option B: Use environment detection:**
   ```javascript
   // Auto-detect API URL based on domain
   const API_BASE_URL = window.location.hostname === 'localhost' 
       ? 'http://localhost:8000'
       : 'https://api.your-domain.com';
   ```

3. **Update CORS in API:**
   ```python
   # In src/api/main.py or via environment variable:
   CORS_ORIGINS=https://your-pwa-domain.com,https://www.your-pwa-domain.com
   ```

#### 3. **Testing**

1. Visit your PWA domain: `https://your-pwa-domain.com`
2. Enter API URL: `https://api.your-domain.com` (or it auto-detects)
3. Fill in filters and submit
4. Check API logs: `pm2 logs avto-scraper` or `journalctl -u avto-scraper`

---

## Scenario 2: Database-Based Authentication (No localStorage)

### Current System (localStorage):
- ✅ User enters credentials once
- ✅ Stored in browser's localStorage
- ✅ Auto-filled on page reload
- ❌ Not shared across devices
- ❌ Lost if browser data cleared

### Database-Based System:
- ✅ Credentials stored server-side
- ✅ Works across devices
- ✅ Persistent storage
- ✅ Can add login/authentication
- ⚠️ Requires authentication system

### Implementation Options:

#### Option A: Simple Session-Based (Recommended for Start)

**1. Add Login Endpoint:**
```python
# In src/api/main.py

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """Login and get session token"""
    user_id = request.user_id
    pushover_api_token = request.pushover_api_token
    pushover_user_key = request.pushover_user_key
    
    # Verify credentials match stored user
    user = user_manager.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if (user['pushover_api_token'] != pushover_api_token or 
        user['pushover_user_key'] != pushover_user_key):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Generate session token (simple version)
    import secrets
    session_token = secrets.token_urlsafe(32)
    
    # Store session in database (add sessions table)
    # Return token to client
    
    return {"session_token": session_token, "user_id": user_id}
```

**2. Add Sessions Table:**
```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    session_token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

**3. Update PWA to:**
- Call `/api/auth/login` on form submit
- Store session token in localStorage (or httpOnly cookie)
- Send session token with each request
- Auto-login if valid session exists

#### Option B: JWT-Based Authentication

**1. Install JWT library:**
```bash
pip install python-jose[cryptography] passlib[bcrypt]
```

**2. Add JWT endpoints:**
```python
from jose import JWTError, jwt
from datetime import datetime, timedelta

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")
ALGORITHM = "HS256"

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    # Verify credentials
    user = user_manager.get_user(request.user_id)
    if not user or user['pushover_api_token'] != request.pushover_api_token:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create JWT token
    expire = datetime.utcnow() + timedelta(days=30)
    token_data = {"sub": request.user_id, "exp": expire}
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    
    return {"access_token": token, "token_type": "bearer"}

@app.get("/api/users/me")
async def get_current_user(token: str = Header(...)):
    """Get current user from JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = user_manager.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user
```

**3. Update PWA:**
- Store JWT token after login
- Send `Authorization: Bearer <token>` header with requests
- Auto-refresh token if expired

---

## Quick Comparison

| Feature | localStorage (Current) | Database Auth |
|---------|----------------------|---------------|
| **Setup Complexity** | ✅ Simple | ⚠️ Moderate |
| **Cross-Device** | ❌ No | ✅ Yes |
| **Security** | ⚠️ Client-side | ✅ Server-side |
| **User Management** | ❌ Manual | ✅ Automatic |
| **Password Reset** | ❌ Not possible | ✅ Possible |
| **Multi-User Support** | ✅ Yes | ✅ Yes |

---

## Recommendation

**For MVP/Start:**
- ✅ Keep localStorage approach
- ✅ Deploy API on Hostinger
- ✅ Deploy PWA on domain
- ✅ Works perfectly for single-user or small scale

**For Production/Scale:**
- ✅ Add database-based authentication
- ✅ Add user registration/login flow
- ✅ Add password reset
- ✅ Add user dashboard
- ✅ Add admin panel

---

## Next Steps

1. **Deploy current system** (localStorage) to Hostinger + domain
2. **Test thoroughly** with real users
3. **Add authentication** when you need:
   - Multi-device support
   - User management
   - Password reset
   - Admin features

Would you like me to implement the database-based authentication system now, or deploy the current system first?

