import os
import yt_dlp
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>X Downloader - Wersja V3</title>
    <style>
        body { font-family: -apple-system, sans-serif; background-color: #15202b; color: white; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .container { background: #192734; padding: 2rem; border-radius: 20px; width: 90%; max-width: 500px; text-align: center; border: 1px solid #38444d; }
        h1 { color: #1d9bf0; }
        input { width: 100%; padding: 15px; margin: 20px 0; border: 1px solid #38444d; border-radius: 9999px; background: #15202b; color: white; box-sizing: border-box; outline: none; }
        button { background: #1d9bf0; color: white; border: none; padding: 15px 40px; border-radius: 9999px; cursor: pointer; font-weight: bold; width: 100%; }
        button:disabled { background: #0e4e78; }
        .video-card { background: #22303c; margin-top: 20px; padding: 15px; border-radius: 15px; text-align: left; }
        .dl-btn { display: block; background: #00ba7c; color: white; text-decoration: none; padding: 10px; border-radius: 8px; text-align: center; margin-top: 10px; font-weight: bold; }
        .loader { border: 3px solid #f3f3f3; border-top: 3px solid #1d9bf0; border-radius: 50%; width: 20px; height: 20px; animation: spin 1s linear infinite; display: inline-block; vertical-align: middle; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="container">
        <h1>X Video Downloader</h1>
        <form id="dlForm">
            <input type="url" id="urlInput" placeholder="Wklej link z X (Twitter)..." required>
            <button type="submit" id="btn">Znajdź wideo</button>
        </form>
        <div id="result"></div>
    </div>

    <script>
        document.getElementById('dlForm').onsubmit = async (e) => {
            e.preventDefault();
            const btn = document.getElementById('btn');
            const res = document.getElementById('result');
            btn.disabled = true;
            btn.innerHTML = '<span class="loader"></span> Analiza...';
            res.innerHTML = '';

            try {
                const response = await fetch('/extract', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: `url=${encodeURIComponent(document.getElementById('urlInput').value)}`
                });
                const data = await response.json();
                if (data.success) {
                    let html = `<div class="video-card"><strong>Tytuł:</strong> ${data.title}<br><br>`;
                    data.formats.forEach(f => {
                        html += `<a href="${f.url}" target="_blank" class="dl-btn">Pobierz ${f.quality} (.mp4)</a>`;
                    });
                    html += `<p style="font-size:11px; color:#8899a6; margin-top:10px;">Jeśli wideo się otworzy zamiast pobrać: kliknij 3 kropki i "Pobierz" lub prawy przycisk myszy i "Zapisz jako".</p></div>`;
                    res.innerHTML = html;
                } else { res.innerHTML = '<p style="color:red">Błąd: ' + data.error + '</p>'; }
            } catch (err) { res.innerHTML = '<p style="color:red">Serwer przeciążony. Spróbuj za chwilę.</p>'; }
            finally { btn.disabled = false; btn.innerText = "Znajdź wideo"; }
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
        'quiet': True,
        'no_warnings': True,
        'format': 'best'
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(target_url, download=False)
            formats_found = []
            
            # Twitter zazwyczaj ma kilka gotowych plików mp4 w różnych rozdzielczościach
            # Szukamy tych, które mają i wideo i audio (acodec != none)
            for f in info.get('formats', []):
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('ext') == 'mp4':
                    formats_found.append({
                        'quality': f"{f.get('width')}x{f.get('height')}",
                        'url': f.get('url'),
                        'size': f.get('filesize', 0)
                    })
            
            # Sortujemy od najlepszej jakości
            formats_found.sort(key=lambda x: int(x['quality'].split('x')[0]) if 'x' in x['quality'] else 0, reverse=True)

            return jsonify({
                'success': True,
                'title': info.get('title', 'Video_X')[:50],
                'formats': formats_found[:3] # Zwróć 3 najlepsze formaty
            })
    except Exception as e:
        return jsonify({'success': False, 'error': "Nie można odczytać wideo. Sprawdź link."})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
