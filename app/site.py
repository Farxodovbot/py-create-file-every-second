<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UC TERMINAL | Official System</title>
    <style>
        body { margin: 0; background: #050505; color: #fff; font-family: 'Inter', sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; overflow-x: hidden; }
        .app-container { width: 95%; max-width: 400px; background: #111; padding: 25px; border-radius: 25px; border: 1px solid #222; text-align: center; box-shadow: 0 0 30px rgba(0,0,0,0.5); }
        .balance-section { background: linear-gradient(145deg, #1a1a1a, #222); padding: 20px; border-radius: 18px; margin-bottom: 20px; border: 1px solid #333; }
        .balance-value { font-size: 38px; font-weight: 800; color: #f39c12; }
        
        /* WHEEL */
        .wheel-box { position: relative; margin: 20px auto; width: 240px; height: 240px; }
        #wheel { width: 100%; height: 100%; border-radius: 50%; border: 6px solid #222; transition: transform 4s cubic-bezier(0.15, 0, 0.15, 1); background: conic-gradient(#ff4d4d 0deg 60deg, #3498db 60deg 120deg, #f1c40f 120deg 180deg, #2ecc71 180deg 240deg, #9b59b6 240deg 300deg, #e67e22 300deg 360deg); }
        .pointer { position: absolute; top: -15px; left: 50%; transform: translateX(-50%); width: 30px; height: 30px; background: #fff; clip-path: polygon(50% 100%, 0 0, 100% 0); z-index: 10; }

        /* BUTTONS */
        .btn-main { display: block; width: 100%; padding: 15px; margin: 8px 0; border-radius: 12px; font-weight: 900; cursor: pointer; font-size: 16px; border: none; transition: 0.3s; box-sizing: border-box; }
        .btn-spin { background: #fff; color: #000; }
        .btn-withdraw { background: #27ae60; color: #fff; }
        .btn-promo { background: transparent; color: #f39c12; border: 1px dashed #f39c12; }
        .btn-main:disabled { background: #222; color: #555; cursor: not-allowed; }
        
        /* MODALS */
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.95); z-index: 100; justify-content: center; align-items: center; }
        .modal-content { background: #1a1a1a; padding: 30px; border-radius: 20px; width: 85%; max-width: 320px; border: 1px solid #333; }
        input { width: 100%; padding: 12px; margin-top: 15px; border-radius: 8px; border: 1px solid #333; background: #000; color: #fff; text-align: center; font-size: 18px; box-sizing: border-box; }
        
        #timer { color: #e74c3c; font-size: 14px; margin-bottom: 10px; display: none; font-weight: bold; }
    </style>
</head>
<body>

<div class="app-container">
    <h2 style="margin:0 0 15px 0; letter-spacing: 2px; color: #f39c12;">UC TERMINAL</h2>
    
    <div class="balance-section">
        <div style="font-size: 11px; color: #888; letter-spacing: 1px;">HISOBINGIZ</div>
        <div class="balance-value"><span id="user-balance">0</span> <span style="font-size: 20px;">UC</span></div>
        <div style="font-size: 11px; color: #555; margin-top: 5px;">Minimal yechish: 360 UC</div>
    </div>

    <div class="wheel-box">
        <div class="pointer"></div>
        <div id="wheel"></div>
    </div>

    <div id="timer">Yangi imkoniyat: <span id="countdown">00:00:00</span></div>
    <button class="btn-main btn-spin" id="spin-btn" onclick="spinWheel()">AYLANTIRISH (3/3)</button>
    <button class="btn-main btn-withdraw" onclick="openWithdraw()">YECHIB OLISH</button>
    <button class="btn-main btn-promo" onclick="openPromo()">PROMOKOD</button>
    
    <div id="msg" style="margin-top: 15px; font-weight: bold; font-size: 14px;"></div>
</div>

<div id="withdraw-modal" class="modal">
    <div class="modal-content">
        <h3 style="margin:0;">PUBG ID YUBORISH</h3>
        <p style="font-size:12px; color:#888;">UC tushishi uchun ID raqamingizni kiriting</p>
        <input type="number" id="pubg-id" placeholder="5123456789">
        <button class="btn-main btn-withdraw" style="margin-top:20px;" onclick="confirmWithdraw()">TASDIQLASH</button>
        <button class="btn-main" style="background:transparent; color:#555;" onclick="closeModals()">Yopish</button>
    </div>
</div>

<div id="promo-modal" class="modal">
    <div class="modal-content">
        <h3 style="margin:0;">PROMOKOD</h3>
        <p style="font-size:12px; color:#888;">Bonus UC olish uchun kodni kiriting</p>
        <input type="text" id="promo-code" placeholder="PROMO2026">
        <button class="btn-main btn-spin" style="margin-top:20px;" onclick="confirmPromo()">FAOL LASHTIRISH</button>
        <button class="btn-main" style="background:transparent; color:#555;" onclick="closeModals()">Yopish</button>
    </div>
</div>

<script>
    // --- ADMIN SOZLAMALARI ---
    const ACTIVE_PROMO = "UZB2026"; // Amaldagi promokod
    const PROMO_VALUE = 50;         // Beriladigan bonus miqdori
    // -------------------------

    let currentRotation = 0;
    const LIMIT = 3;
    const COOLDOWN = 24 * 60 * 60 * 1000;

    let data = JSON.parse(localStorage.getItem('uc_master_v5')) || {
        balance: 0, tries: LIMIT, lastTime: 0, usedPromo: false
    };

    function updateUI() {
        document.getElementById('user-balance').innerText = data.balance;
        document.getElementById('spin-btn').innerText = `AYLANTIRISH (${data.tries}/${LIMIT})`;
        checkTime();
    }

    function checkTime() {
        const now = Date.now();
        if (data.tries <= 0) {
            const passed = now - data.lastTime;
            if (passed >= COOLDOWN) {
                data.tries = LIMIT;
                save();
                location.reload();
            } else {
                document.getElementById('spin-btn').disabled = true;
                document.getElementById('timer').style.display = 'block';
                runTimer(COOLDOWN - passed);
            }
        }
    }

    function runTimer(ms) {
        const cd = document.getElementById('countdown');
        const itv = setInterval(() => {
            ms -= 1000;
            if (ms <= 0) { clearInterval(itv); location.reload(); }
            let h = Math.floor(ms / 3600000);
            let m = Math.floor((ms % 3600000) / 60000);
            let s = Math.floor((ms % 60000) / 1000);
            cd.innerText = `${h.toString().padStart(2,'0')}:${m.toString().padStart(2,'0')}:${s.toString().padStart(2,'0')}`;
        }, 1000);
    }

    function spinWheel() {
        if (data.tries <= 0) return;
        data.tries--;
        if (data.tries === 0) data.lastTime = Date.now();
        save();
        
        document.getElementById('spin-btn').disabled = true;
        const deg = Math.floor(Math.random() * 360);
        currentRotation += 1440 + deg;
        document.getElementById('wheel').style.transform = `rotate(${currentRotation}deg)`;

        setTimeout(() => {
            const prizes = [10, 50, 0, 100, 20, 5];
            const win = prizes[Math.floor(Math.random() * prizes.length)];
            data.balance += win;
            save();
            document.getElementById('msg').innerText = win > 0 ? `+${win} UC YUTDINGIZ!` : "OMAD KELMADI";
            document.getElementById('msg').style.color = win > 0 ? "#2ecc71" : "#e74c3c";
            updateUI();
            if (data.tries > 0) document.getElementById('spin-btn').disabled = false;
        }, 4000);
    }

    // Modal funksiyalari
    function openWithdraw() {
        if (data.balance < 360) alert(`Minimal 360 UC kerak! Sizda: ${data.balance}`);
        else document.getElementById('withdraw-modal').style.display = 'flex';
    }
    function openPromo() { document.getElementById('promo-modal').style.display = 'flex'; }
    function closeModals() { 
        document.getElementById('withdraw-modal').style.display = 'none';
        document.getElementById('promo-modal').style.display = 'none';
    }

    function confirmWithdraw() {
        const id = document.getElementById('pubg-id').value;
        if (id.length < 5) return alert("ID xato!");
        alert(`Muvaffaqiyatli! ID: ${id} raqamiga ${data.balance} UC yuborildi.`);
        data.balance = 0;
        save();
        location.reload();
    }

    function confirmPromo() {
        const code = document.getElementById('promo-code').value;
        if (data.usedPromo) return alert("Siz promokod ishlatgansiz!");
        if (code === ACTIVE_PROMO) {
            data.balance += PROMO_VALUE;
            data.usedPromo = true;
            save();
            alert(`Tabriklaymiz! +${PROMO_VALUE} UC bonus berildi.`);
            location.reload();
        } else {
            alert("Promokod xato!");
        }
    }

    function save() { localStorage.setItem('uc_master_v5', JSON.stringify(data)); }
    updateUI();
</script>
</body>
</html>
