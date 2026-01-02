import os
import requests
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>X Downloader - V4 Fixed</title>
    <style>
        body { font-family: -apple-system, sans-serif; background-color: #15202b; color: white; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .container { background: #192734; padding: 2rem; border-radius: 20px; width: 90%; max-width: 500px; text-align: center; border: 1px solid #38444d; }
        h1 { color: #1d9bf0; }
        input { width: 100%; padding: 15px; margin: 20px 0; border: 1px solid #38444d; border-radius: 9999px; background: #15202b; color: white; box-sizing: border-box; outline: none; }
        button { background: #1d9bf0; color: white; border: none; padding: 15px 40px; border-radius: 9999px; cursor: pointer; font-weight: bold; width: 100%; }
        .result-box { background: #22303c; margin-top: 20px; padding: 20px; border-radius: 15px; text-align: left; }
        .dl-btn { display: block; background: #00ba7c; color: white; text-decoration: none; padding: 12px; border-radius: 8px; text-align: center; margin-top: 10px; font-weight: bold; }
        .loader { border: 3px solid #f3f3f3; border-top: 3px solid #1d9bf0; border-radius: 50%; width: 20px; height: 20px; animation: spin 1s linear infinite; display: inline-block; vertical-align: middle; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="container">
        <h1>X Downloader</h1>
        <p>Metoda hybrydowa (Fix Unauthorized)</p>
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
            btn.innerHTML = '<span class="loader"></span> Omijanie blokady...';
            
            try {
                const response = await fetch('/extract', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: `url=${encodeURIComponent(document.getElementById('urlInput').value)}`
                });
                const data = await response.json();
                
                if (data.success) {
                    res.innerHTML = `
                        <div class="result-box">
                            <strong>Wideo gotowe!</strong>
                            <a href="${data.url}" rel="noreferrer" target="_blank" class="dl-btn">POBIERZ MP4 (${data.quality})</a>
                            <p style="font-size:11px; color:#8899a6; margin-top:10px;">Jeśli otworzy się w nowym oknie: kliknij prawy przycisk myszy i "Zapisz jako".</p>
                        </div>`;
                } else {
                    res.innerHTML = '<p style="color:#e0245e">Błąd: Twitter zablokował IP serwera. Spróbuj za chwilę.</p>';
                }
            } catch (err) { res.innerHTML = 'Błąd połączenia.'; }
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
    
    # Używamy zewnętrznego API (publer), które rzadko jest blokowane przez X
    # To API wyciąga linki bez potrzeby posiadania tokenów na Twoim serwerze
    api_url = "https://publer.io/api/v1/twitter/video"
    
    try:
        # Symulujemy zapytanie z przeglądarki do zewnętrznego silnika
        payload = {"url": target_url}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/114.0.0.0 Safari/537.36",
            "Referer": "https://publer.io/twitter-video-downloader"
        }
        
        r = requests.post(api_url, json=payload, headers=headers, timeout=15)
        data = r.json()
        
        # Wybieramy najlepszą jakość z listy
        if data.get('urls'):
            best_video = data['urls'][0] # Publer zazwyczaj sortuje od najlepszej jakości
            return jsonify({
                'success': True,
                'url': best_video['url'],
                'quality': best_video.get('quality', 'HD')
            })
        else:
            return jsonify({'success': False, 'error': 'Nie znaleziono wideo.'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': 'Blokada API. Spróbuj ponownie później.'})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
