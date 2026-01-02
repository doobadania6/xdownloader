import os
import requests
import yt_dlp
from flask import Flask, render_template_string, request, jsonify, redirect

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>X Downloader - Szybka Wersja</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #15202b; color: white; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .container { background: #192734; padding: 2rem; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); width: 90%; max-width: 500px; text-align: center; border: 1px solid #38444d; }
        h1 { color: #1d9bf0; }
        input { width: 100%; padding: 15px; margin: 20px 0; border: 1px solid #38444d; border-radius: 9999px; background: #15202b; color: white; font-size: 16px; box-sizing: border-box; outline: none; }
        button { background: #1d9bf0; color: white; border: none; padding: 15px 40px; border-radius: 9999px; cursor: pointer; font-weight: bold; font-size: 16px; width: 100%; }
        button:disabled { background: #0e4e78; }
        #result { margin-top: 30px; }
        .download-btn { display: block; background: #00ba7c; color: white; text-decoration: none; padding: 15px; border-radius: 10px; font-weight: bold; margin-top: 10px; }
        .loader { border: 3px solid #f3f3f3; border-top: 3px solid #1d9bf0; border-radius: 50%; width: 20px; height: 20px; animation: spin 1s linear infinite; display: inline-block; vertical-align: middle; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="container">
        <h1>X Video Downloader</h1>
        <p>Szybka analiza linku...</p>
        <form id="dlForm">
            <input type="url" id="urlInput" placeholder="Wklej link z X..." required>
            <button type="submit" id="btn">Przygotuj Pobieranie</button>
        </form>
        <div id="result"></div>
    </div>

    <script>
        document.getElementById('dlForm').onsubmit = async (e) => {
            e.preventDefault();
            const btn = document.getElementById('btn');
            const result = document.getElementById('result');
            btn.disabled = true;
            btn.innerHTML = '<span class="loader"></span> Pobieranie danych...';
            
            try {
                const response = await fetch('/extract', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: `url=${encodeURIComponent(document.getElementById('urlInput').value)}`
                });
                const data = await response.json();
                if (data.success) {
                    result.innerHTML = `
                        <p style="font-size:14px; color:#8899a6;">Jakość: ${data.quality}</p>
                        <a href="${data.url}" target="_blank" class="download-link">KLIKNIJ ABY POBRAĆ MP4</a>
                        <p style="font-size:12px; color:#8899a6; margin-top:10px;">Jeśli otworzy się w nowym oknie: prawy przycisk myszy -> Zapisz jako.</p>
                    `;
                } else { alert("Błąd: " + data.error); }
            } catch (err) { alert("Błąd połączenia."); }
            finally { btn.disabled = false; btn.innerText = "Przygotuj Pobieranie"; }
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
    
    # Używamy prostego formatu, który nie wymaga łączenia obrazu i dźwięku (aby uniknąć kręcenia)
    ydl_opts = {
        'format': 'best[ext=mp4]', 
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(target_url, download=False)
            video_url = info.get('url')
            
            # Jeśli video_url zawiera link do Twittera, musimy go przepuścić przez nasz uproszczony proxy
            # Ale tym razem zrobimy to bez streamingu, który zawiesza serwer
            quality = f"{info.get('width', '???')}x{info.get('height', '???')}"
            
            return jsonify({
                'success': True, 
                'url': video_url, # Przekazujemy bezpośredni link
                'quality': quality
            })
    except Exception as e:
        return jsonify({'success': False, 'error': "Nie udało się pobrać danych. Spróbuj inny link."})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
