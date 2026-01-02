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
    <title>X Downloader - Final Fix</title>
    <style>
        body { font-family: -apple-system, sans-serif; background-color: #15202b; color: white; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .container { background: #192734; padding: 2rem; border-radius: 20px; width: 90%; max-width: 500px; text-align: center; border: 1px solid #38444d; }
        h1 { color: #1d9bf0; margin-bottom: 5px; }
        p { color: #8899a6; font-size: 14px; }
        input { width: 100%; padding: 15px; margin: 20px 0; border: 1px solid #38444d; border-radius: 9999px; background: #15202b; color: white; box-sizing: border-box; outline: none; }
        button { background: #1d9bf0; color: white; border: none; padding: 15px 40px; border-radius: 9999px; cursor: pointer; font-weight: bold; width: 100%; }
        button:disabled { background: #0e4e78; }
        .result-box { background: #22303c; margin-top: 20px; padding: 20px; border-radius: 15px; text-align: left; border: 1px solid #1d9bf0; }
        .quality-item { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; padding: 10px; background: #192734; border-radius: 8px; }
        .dl-btn { background: #00ba7c; color: white; text-decoration: none; padding: 8px 15px; border-radius: 5px; font-weight: bold; font-size: 13px; }
        .loader { border: 3px solid #f3f3f3; border-top: 3px solid #1d9bf0; border-radius: 50%; width: 20px; height: 20px; animation: spin 1s linear infinite; display: inline-block; vertical-align: middle; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="container">
        <h1>X Downloader</h1>
        <p>Jeśli wyskakuje błąd, odśwież stronę i spróbuj ponownie.</p>
        <form id="dlForm">
            <input type="url" id="urlInput" placeholder="Wklej link do posta z X..." required>
            <button type="submit" id="btn">Analizuj wideo</button>
        </form>
        <div id="result"></div>
    </div>

    <script>
        document.getElementById('dlForm').onsubmit = async (e) => {
            e.preventDefault();
            const res = document.getElementById('result');
            const btn = document.getElementById('btn');
            btn.disabled = true;
            btn.innerHTML = '<span class="loader"></span> Omijanie blokad...';
            
            try {
                const response = await fetch('/extract', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: `url=${encodeURIComponent(document.getElementById('urlInput').value)}`
                });
                const data = await response.json();
                
                if (data.success) {
                    let html = '<div class="result-box"><strong>Dostępne jakości:</strong><br><br>';
                    data.formats.forEach(f => {
                        html += `
                        <div class="quality-item">
                            <span>${f.quality}</span>
                            <a href="${f.url}" rel="noreferrer" target="_blank" class="dl-btn">POBIERZ</a>
                        </div>`;
                    });
                    html += '<p style="font-size:11px; color:#8899a6; margin-top:10px;">Kliknij prawym przyciskiem i "Zapisz jako", jeśli film się tylko odtwarza.</p></div>';
                    res.innerHTML = html;
                } else {
                    res.innerHTML = '<p style="color:#e0245e">Błąd: Twitter blokuje serwer. Spróbuj za chwilę lub użyj innego linku.</p>';
                }
            } catch (err) { res.innerHTML = 'Błąd serwera.'; }
            finally { btn.disabled = false; btn.innerText = "Analizuj wideo"; }
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
    target_url = request.form.get('url').replace('x.com', 'twitter.com')
    
    # Konfiguracja udająca oficjalną aplikację Twittera
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'best',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Connection': 'keep-alive',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Próba pobrania informacji bez pobierania pliku
            info = ydl.extract_info(target_url, download=False)
            formats_list = []
            
            # Twitter serwuje różne rozdzielczości w MP4
            for f in info.get('formats', []):
                # Szukamy formatów, które mają audio i wideo i są w mp4
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and 'mp4' in f.get('ext', ''):
                    formats_list.append({
                        'quality': f"{f.get('height')}p",
                        'url': f.get('url'),
                        'res': f.get('height', 0)
                    })
            
            # Sortuj od najwyższej jakości
            formats_list.sort(key=lambda x: x['res'], reverse=True)
            
            # Usuń duplikaty rozdzielczości
            seen = set()
            unique_formats = []
            for f in formats_list:
                if f['quality'] not in seen:
                    unique_formats.append(f)
                    seen.add(f['quality'])

            return jsonify({
                'success': True,
                'formats': unique_formats[:3] # Zwróć 3 najlepsze
            })
    except Exception as e:
        print(f"Błąd: {e}")
        return jsonify({'success': False, 'error': "Unauthorized"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
