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
    <title>X Downloader - Fix 403</title>
    <style>
        body { font-family: -apple-system, sans-serif; background-color: #15202b; color: white; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .container { background: #192734; padding: 2rem; border-radius: 20px; width: 90%; max-width: 500px; text-align: center; border: 1px solid #38444d; }
        h1 { color: #1d9bf0; }
        input { width: 100%; padding: 15px; margin: 20px 0; border: 1px solid #38444d; border-radius: 9999px; background: #15202b; color: white; box-sizing: border-box; outline: none; }
        button { background: #1d9bf0; color: white; border: none; padding: 15px 40px; border-radius: 9999px; cursor: pointer; font-weight: bold; width: 100%; }
        #result { margin-top: 20px; }
        .dl-btn { display: block; background: #00ba7c; color: white; text-decoration: none; padding: 15px; border-radius: 10px; font-weight: bold; }
        .loader { border: 3px solid #f3f3f3; border-top: 3px solid #1d9bf0; border-radius: 50%; width: 20px; height: 20px; animation: spin 1s linear infinite; display: inline-block; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="container">
        <h1>X Downloader PRO</h1>
        <form id="dlForm">
            <input type="url" id="urlInput" placeholder="Wklej link z X..." required>
            <button type="submit" id="btn">Pobierz wideo</button>
        </form>
        <div id="result"></div>
    </div>

    <script>
        document.getElementById('dlForm').onsubmit = async (e) => {
            e.preventDefault();
            const res = document.getElementById('result');
            const btn = document.getElementById('btn');
            btn.disabled = true;
            btn.innerHTML = '<span class="loader"></span> Omijanie blokady 403...';
            
            try {
                const response = await fetch('/extract', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: `url=${encodeURIComponent(document.getElementById('urlInput').value)}`
                });
                const data = await response.json();
                if (data.success) {
                    res.innerHTML = `<a href="${data.proxy_url}" class="dl-btn">ZAPISZ WIDEO NA DYSKU</a>`;
                } else { res.innerHTML = '<p style="color:red">Błąd autoryzacji Twittera. Spróbuj ponownie.</p>'; }
            } catch (err) { res.innerHTML = 'Błąd serwera.'; }
            finally { btn.disabled = false; btn.innerText = "Pobierz wideo"; }
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
    ydl_opts = {'format': 'best[ext=mp4]', 'quiet': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(target_url, download=False)
            video_url = info.get('url')
            # Tworzymy link do naszego wewnętrznego tunelu
            proxy_url = f"/proxy_video?url={requests.utils.quote(video_url)}"
            return jsonify({'success': True, 'proxy_url': proxy_url})
    except:
        return jsonify({'success': False})

@app.route('/proxy_video')
def proxy_video():
    video_url = request.args.get('url')
    
    # Nagłówki, które sprawią, że Twitter "zaufa" serwerowi Render
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Referer': 'https://twitter.com/',
        'Accept': '*/*'
    }

    def generate():
        # Serwer pobiera dane z Twittera i natychmiast przekazuje je Tobie
        with requests.get(video_url, headers=headers, stream=True) as r:
            for chunk in r.iter_content(chunk_size=1024*1024):
                yield chunk

    return Response(stream_with_context(generate()), mimetype='video/mp4', headers={
        "Content-Disposition": "attachment; filename=video_x.mp4"
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
