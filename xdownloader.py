import os
import requests
import yt_dlp
from flask import Flask, render_template_string, request, jsonify, Response, stream_with_context

app = Flask(__name__)

# Nowoczesny interfejs w stylu "X Dark Mode"
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>X Video Downloader - FULL HD</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #15202b; color: white; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .container { background: #192734; padding: 2rem; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); width: 90%; max-width: 500px; text-align: center; border: 1px solid #38444d; }
        h1 { color: #1d9bf0; margin-bottom: 0.5rem; }
        .quality-badge { background: #e0245e; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; vertical-align: middle; }
        p { color: #8899a6; margin-bottom: 20px; }
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
        <h1>X Downloader <span class="quality-badge">1080p</span></h1>
        <p>Pobieranie w najwyższej dostępnej jakości.</p>
        <form id="dlForm">
            <input type="url" id="urlInput" placeholder="Wklej link do posta z X (Twitter)..." required>
            <button type="submit" id="btn">Analizuj i pobierz</button>
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
            btn.innerHTML = '<span class="loader"></span> Szukam najwyższej jakości...';
            result.classList.add('hidden');
            
            try {
                const response = await fetch('/extract', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: `url=${encodeURIComponent(document.getElementById('urlInput').value)}`
                });
                const data = await response.json();
                if (data.success) {
                    result.innerHTML = `
                        <div style="text-align:left; background:#22303c; padding:15px; border-radius:10px;">
                            <p style="color:white; margin:0 0 10px 0;"><strong>Wideo gotowe:</strong> ${data.title}</p>
                            <a href="${data.url}" class="download-link">POBIERZ PLIK MP4 (MAX QUALITY)</a>
                        </div>`;
                    result.classList.remove('hidden');
                } else { alert("Błąd: " + data.error); }
            } catch (err) { alert("Błąd serwera."); }
            finally { btn.disabled = false; btn.innerText = "Analizuj i pobierz"; }
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
    
    # FORMAT: Szukamy najlepszego wideo i najlepszego audio, preferujemy mp4
    # Jeśli 1080p jest dostępne jako jeden plik, zostanie wybrane.
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
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
            # Jeśli yt-dlp znajdzie rozdzielone strumienie bez ffmpeg, weźmie najlepszy gotowy
            title = "".join([x for x in info.get('title', 'video') if x.isalnum() or x==' '])[:50]
            
            safe_url = requests.utils.quote(video_url)
            download_proxy_url = f"/stream_video?url={safe_url}&title={title}"
            
            return jsonify({'success': True, 'url': download_proxy_url, 'title': title})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/stream_video')
def stream_video():
    video_url = request.args.get('url')
    title = request.args.get('title', 'video')
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://x.com/',
        'Accept': 'video/webm,video/ogg,video/*;q=0.9,*/*;q=0.5',
        'Connection': 'keep-alive',
    }

    def generate():
        with requests.get(video_url, headers=headers, stream=True, timeout=120) as r:
            r.raise_for_status()
            # Przesyłamy w kawałkach 128KB dla stabilności przy wysokiej jakości
            for chunk in r.iter_content(chunk_size=131072):
                if chunk:
                    yield chunk

    return Response(
        stream_with_context(generate()),
        mimetype='video/mp4',
        headers={"Content-disposition": f"attachment; filename={title}.mp4"}
    )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
