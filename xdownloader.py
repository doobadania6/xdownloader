import os
import requests
import yt_dlp
from flask import Flask, render_template_string, request, jsonify, Response, stream_with_context

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>X Video Downloader - Stabilny</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #15202b; color: white; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .container { background: #192734; padding: 2rem; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); width: 90%; max-width: 500px; text-align: center; border: 1px solid #38444d; }
        h1 { color: #1d9bf0; margin-bottom: 1rem; }
        input { width: 100%; padding: 15px; margin: 20px 0; border: 1px solid #38444d; border-radius: 9999px; background: #15202b; color: white; font-size: 16px; box-sizing: border-box; outline: none; }
        input:focus { border-color: #1d9bf0; }
        button { background: #1d9bf0; color: white; border: none; padding: 15px 40px; border-radius: 9999px; cursor: pointer; font-weight: bold; font-size: 16px; width: 100%; transition: 0.2s; }
        button:hover { background: #1a8cd8; }
        button:disabled { background: #0e4e78; cursor: not-allowed; }
        #result { margin-top: 30px; border-top: 1px solid #38444d; padding-top: 20px; }
        .download-link { display: block; background: #00ba7c; color: white; text-decoration: none; padding: 15px; border-radius: 10px; font-weight: bold; margin-top: 10px; }
        .loader { border: 3px solid #f3f3f3; border-top: 3px solid #1d9bf0; border-radius: 50%; width: 20px; height: 20px; animation: spin 1s linear infinite; display: inline-block; vertical-align: middle; margin-right: 10px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .hidden { display: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>X Downloader PRO</h1>
        <p>Jeśli pobieranie nie rusza, spróbuj ponownie za chwilę.</p>
        <form id="dlForm">
            <input type="url" id="urlInput" placeholder="Wklej link do posta z X (Twitter)..." required>
            <button type="submit" id="btn">Wygeneruj MP4</button>
        </form>
        <div id="result" class="hidden"></div>
    </div>

    <script>
        const form = document.getElementById('dlForm');
        const btn = document.getElementById('btn');
        const result = document.getElementById('result');

        form.onsubmit = async (e) => {
            e.preventDefault();
            btn.disabled = true;
            btn.innerHTML = '<span class="loader"></span> Analizuję...';
            result.classList.add('hidden');
            
            try {
                const response = await fetch('/extract', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: `url=${encodeURIComponent(document.getElementById('urlInput').value)}`
                });
                const data = await response.json();
                if (data.success) {
                    result.innerHTML = `<a href="${data.url}" class="download-link">POBIERZ I ZAPISZ WIDEO</a>`;
                    result.classList.remove('hidden');
                } else { alert("Błąd: " + data.error); }
            } catch (err) { alert("Błąd serwera."); }
            finally { btn.disabled = false; btn.innerText = "Wygeneruj MP4"; }
        };
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/extract', methods=['POST'])
def extract():
    target_url = request.form.get('url')
    
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        # Udajemy przeglądarkę na poziomie yt-dlp
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Referer': 'https://x.com/',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(target_url, download=False)
            video_url = info.get('url')
            title = "".join([x for x in info.get('title', 'video') if x.isalnum()])[:30]
            
            # Kodujemy URL, aby bezpiecznie przesłać go w parametrze
            safe_url = requests.utils.quote(video_url)
            download_proxy_url = f"/stream_video?url={safe_url}&title={title}"
            
            return jsonify({'success': True, 'url': download_proxy_url})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/stream_video')
def stream_video():
    video_url = request.args.get('url')
    title = request.args.get('title', 'video')
    
    # Rozbudowane nagłówki, by oszukać system Unauthorized
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://x.com/',
        'Accept': 'video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'video',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
    }

    def generate():
        # Pobieramy z dużym timeoutem
        with requests.get(video_url, headers=headers, stream=True, timeout=60) as r:
            r.raise_for_status()
            for chunk in r.iter_content(chunk_size=65536): # 64KB chunks dla stabilności
                if chunk:
                    yield chunk

    try:
        return Response(
            stream_with_context(generate()),
            mimetype='video/mp4',
            headers={"Content-disposition": f"attachment; filename={title}.mp4"}
        )
    except Exception as e:
        return f"Błąd strumieniowania: {e}", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
