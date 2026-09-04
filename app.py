from flask import Flask, request, Response
import requests
from urllib.parse import urljoin
import random

app = Flask(__name__)

@app.route('/')
def generate_playlist():
    # URL parameters lena
    host = request.args.get('host')
    user = request.args.get('user')
    password = request.args.get('pass')
    channel_id = request.args.get('id')

    if not all([host, user, password, channel_id]):
        return "Error: Missing parameters! Example: /?host=http://5dtv.cc&user=112256&pass=02101994&id=150480", 400

    source_url = f"{host}/live/{user}/{password}/{channel_id}.m3u8"

    # Jio/Airtel ki ek fake mobile IP banana (Anti-block)
    fake_ip = f"106.{random.randint(10, 200)}.{random.randint(0, 255)}.{random.randint(0, 255)}"

    headers = {
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 10; IN1 Build/QP1A.190711.020)",
        "Accept": "*/*",
        "X-Forwarded-For": fake_ip,
        "X-Real-IP": fake_ip,
        "Connection": "keep-alive"
    }

    try:
        # requests.get automatically 302 redirects follow karta hai
        # stream=False rakha hai taaki sirf playlist fetch ho
        response = requests.get(source_url, headers=headers, timeout=10, allow_redirects=True)
        
        if response.status_code != 200:
            return f"#EXTM3U\n# Error fetching stream: HTTP {response.status_code}", 500

        # Redirect hone ke baad jo final IP:8080 wala URL milega
        final_url = response.url 
        
        lines = response.text.splitlines()
        output = []

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith('#'):
                output.append(line)
            else:
                # Relative .ts file ko Absolute URL banata hai (automatically Base URL nikal kar)
                absolute_url = urljoin(final_url, line)
                output.append(absolute_url)

        # CORS allow karne ke liye extra headers add karna
        resp = Response("\n".join(output) + "\n", mimetype='text/plain')
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    except requests.exceptions.RequestException as e:
        return f"#EXTM3U\n# Error: {str(e)}", 500

# Render gunicorn use karega, ye sirf local testing ke liye hai
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
