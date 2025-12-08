
import requests
# --- CONFIG ---
# Ensure NO trailing slash
URL = "https://ollama.bencombs.art/api/tags" 
USER = "admin"
PASS = "011iv3r0329!" 

print(f"--- DIAGNOSTIC MODE ---")
print(f"Target: {URL}")

try:
    # 1. We create a Session (stores cookies/auth persistence better)
    s = requests.Session()
    s.auth = (USER, PASS)
    
    # 2. We spoof a Browser User-Agent (just in case)
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
    })

    # 3. Make the request
    response = s.get(URL)

    # --- ANALYSIS ---
    print(f"\nFinal Status Code: {response.status_code}")
    
    # CHECK FOR REDIRECTS (The #1 Culprit)
    if response.history:
        print("\n⚠️ REDIRECT DETECTED! (This usually strips passwords)")
        for step in response.history:
            print(f"   - Redirected from: {step.url} ({step.status_code})")
            print(f"   - Auth Header sent? {'Authorization' in step.request.headers}")
    else:
        print("\nNo redirects occurred (Good).")

    # CHECK SERVER HEADERS
    print(f"\nServer Response Headers:")
    print(f"   - Server: {response.headers.get('Server', 'Unknown')}")
    print(f"   - WWW-Authenticate: {response.headers.get('WWW-Authenticate', 'None')}")

    # CHECK BODY
    if response.status_code == 401:
        print("\n❌ STILL 401. The Server said:")
        print(response.text[:200]) # Print first 200 chars
    elif response.status_code == 200:
        print("\n✅ SUCCESS! Models found:")
        print(response.json())

except Exception as e:
    print(f"\n❌ CRASHED: {e}")