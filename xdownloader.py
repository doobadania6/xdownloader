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
    <title>X Downloader - Wersja Stabilna</title>
    <style>
        body { font-family: -apple-system, sans-serif; background-color: #15202b; color: white; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .container { background: #192734; padding: 2rem; border-radius: 20px; width: 90%; max-width: 500px; text-align: center; border: 1px solid #38444d; }
        h1 { color: #1d9bf0; margin-bottom: 20px; }
        input { width: 100%; padding: 15px; margin-bottom: 20px; border: 1px solid #38444d; border-radius: 9999px; background: #15202b; color: white; box-sizing: border-box; outline: none; }
        button { background: #1d9bf0; color: white; border: none; padding: 15px 40px; border-radius: 9999px; cursor: pointer; font-weight: bold; width: 100%; font-size: 16px; }
        button:disabled { background: #0e4e78; opacity: 0.7; }
        #result { margin-top: 25px; min-height: 50px; }
        .dl-btn { display: block; background: #00ba7c; color: white; text-decoration: none; padding: 15px; border-radius: 12px; font-weight: bold; margin-top: 10px; transition: 0.3s; }
        .dl-btn:hover { background: #009664; }
        .loader { border: 3px solid #f3f3f3; border-top: 3px solid #1d9bf0; border-radius: 50%; width: 20px; height: 20px; animation: spin 1s linear infinite; display: inline-block; vertical-align: middle; margin-right: 10px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="container">
        <h1>X Video Downloader</h1>
        <form id="dlForm">
            <input type="url" id="urlInput" placeholder="Wklej link do posta z X (Twitter)..." required>
            <button type="submit" id="btn">Pobierz Wideo</button>
        </form>
        <div id="result"></div>
    </div>

    <script>
        document.getElementById('dlForm').onsubmit = async (e) => {
            e.preventDefault();
            const resDiv = document.getElementById('result');
            const btn = document.getElementById('btn');
            const urlValue = document.getElementById('urlInput').value;

            btn.disabled = true;
            btn.innerHTML = '<span class="loader"></span> Trwa omijanie blokad...';
            resDiv.innerHTML = '';
            
            try {
                const response = await fetch('/extract', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: 'url=' + encodeURIComponent(urlValue)
                });
                
                const data = await response.json();
                
                if (data.success && data.proxy_url) {
                    resDiv.innerHTML = `
                        <div style="background: #22303c; padding: 15px; border-radius: 15px;">
                            <p style="margin: 0 0 10px 0; font-size: 14px; color: #8899a6;">Wideo gotowe do pobrania:</p>
                            <a href="${data.proxy_url}" class="dl-btn">ZAPISZ PLIK MP4</a>
                        </div>`;
                } else {
                    resDiv.innerHTML = '<p style="color:#e0245e;">Błąd: Twitter odrzucił połączenie. Spróbuj za chwilę.</p>';
                }
            } catch (err) {
                resDiv.innerHTML = '<p style="color:#e0245e;">Błąd serwera. Odśwież stronę.</p>';
            } finally {
                btn.disabled = false;
                btn.innerText = "Pobierz Wideo";
            }
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
    if not target_url:
        return jsonify({'success': False, 'error': 'No URL provided'})

    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(target_url, download=False)
            video_url = info.get('url')
            
            if not video_url:
                return jsonify({'success': False, 'error': 'Could not find video URL'})

            # Naprawione tworzenie linku proxy (brak szansy na undefined)
            proxy_url = f"/stream?v_url={requests.utils.quote(video_url)}"
            return jsonify({'success': True, 'proxy_url': proxy_url})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/stream')
def stream():
    video_url = request.args.get('v_url')
    if not video_url:
        return "Brak URL", 400

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://twitter.com/',
    }

    def generate():
        # Streamowanie pliku w kawałkach, co oszczędza RAM serwera i omija blokady
        with requests.get(video_url, headers=headers, stream=True, timeout=60) as r:
            r.raise_for_status()
            for chunk in r.iter_content(chunk_size=128*1024): # 128KB kawałki
                yield chunk

    return Response(
        stream_with_context(generate()),
        mimetype='video/mp4',
        headers={"Content-Disposition": "attachment; filename=video_x.mp4"}
    )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
