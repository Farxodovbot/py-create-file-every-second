<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UC TERMINAL | Official</title>
    <style>
        body { margin: 0; background: #050505; color: #fff; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .app-container { width: 90%; max-width: 380px; background: #111; padding: 20px; border-radius: 30px; border: 1px solid #222; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.8); }
        
        /* Balans qismi */
        .balance-card { background: linear-gradient(135deg, #1a1a1a, #252525); padding: 15px; border-radius: 20px; margin-bottom: 20px; border: 1px solid #333; }
        .balance-value { font-size: 40px; font-weight: 800; color: #f39c12; text-shadow: 0 0 15px rgba(243, 156, 18, 0.3); }
        .limit-info { font-size: 11px; color: #666; margin-top: 5px; }

        /* Baraban dizayni */
        .wheel-outer { position: relative; width: 250px; height: 250px; margin: 20px auto; border: 8px solid #1a1a1a; border-radius: 50%; box-shadow: 0 0 20px rgba(0,0,0,0.5); }
        #wheel { width: 100%; height: 100%; border-radius: 50%; transition: transform 4s cubic-bezier(0.15, 0, 0.15, 1); 
            background: conic-gradient(
                #e74c3c 0deg 60deg, #3498db 60deg 120deg, #f1c40f 120deg 180deg, 
                #2ecc71 180deg 240deg, #9b59b6 240deg 300deg, #e67e22 300deg 360deg
            );
        }
        .pointer { position: absolute; top: -10px; left: 50%; transform: translateX(-50%); width: 0; height: 0; border-left: 15px solid transparent; border-right: 15px solid transparent; border-top: 25px solid #fff; z-index: 10; }

        /* Tugmalar */
        .btn { display: block; width: 100%; padding: 15px; margin: 10px 0; border-radius: 15px; font-weight: 700; cursor: pointer; border: none; font-size: 16px; transition: 0.2s; }
        .btn-spin { background: #fff; color: #000; }
        .btn-spin:active { transform: scale(0.98); }
        .btn-withdraw { background: #27ae60; color: #fff; }
        .btn-promo { background: transparent; color: #f39c12; border: 1px dashed #f39c12; margin-top: 5px; font-size: 14px; }
        .btn:disabled { background: #222; color: #555; cursor: not-allowed; }

        /* Modallar (Popup) */
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); z-index: 100; justify-content: center; align-items: center; }
        .modal-content { background: #1a1a1a; padding: 25px; border-radius: 20px; width: 80%; border: 1px solid #333; text-align: center; }
        input { width: 100%; padding: 12px; margin-top: 15px; border-radius: 10px; border: 1px solid #333; background: #000; color: #fff; text-align: center; font-size: 18px; outline: none; }
        
        #timer { color: #ff4d4d; font-size: 14px; margin-bottom: 10px; display: none; font-weight: bold; }
    </style>
</head>
<body>

<div class="app-container">
    <h2 style="margin-bottom: 10px; letter-spacing: 1px;">UC TERMINAL</h2>
    
    <div class="balance-card">
        <div style="font-size: 12px; color: #aaa;">HISOBINGIZ</div>
        <div class="balance-value"><span id="balance-num">0</span> UC</div>
        <div class="limit-info">Yechib olish uchun minimal 360 UC kerak</div>
    </div>

    <div class="wheel-outer">
        <div class="pointer"></div>
        <div id="wheel"></div>
    </div>

    <div id="timer">Keyingi imkoniyat: <span id="countdown">00:00:00</span></div>
    
    <button class="btn btn-spin" id="spin-btn" onclick="spinWheel()">AYLANTIRISH (3/3)</button>
    <button class="btn btn-withdraw" onclick="openWithdraw()">YECHIB OLISH</button>
    <button class="btn btn-promo" onclick="openPromo()">PROMOKOD KIRITISH</button>
    
    <div id="status-msg" style="margin-top: 10px; font-size: 14px; min-height: 20px;"></div>
</div>

<div id="withdraw-modal" class="modal">
    <div class="modal-content">
        <h3 style="margin: 0;">PUBG ID</h3>
        <p style="font-size: 12px; color: #888;">UC tushishi uchun ID raqamingizni yozing</p>
        <input type="number" id="player-id" placeholder="5432106789">
        <button class="btn btn-withdraw" style="margin-top: 20px;" onclick="finishWithdraw()">TASDIQLASH</button>
        <button class="btn" style="background: transparent; color: #666;" onclick="closeModals()">Yopish</button>
    </div>
</div>

<div id="promo-modal" class="modal">
    <div class="modal-content">
        <h3 style="margin: 0;">PROMOKOD</h3>
        <p style="font-size: 12px; color: #888;">Maxsus bonus UC olish</p>
        <input type="text" id="promo-input" placeholder="KODNI YOZING">
        <button class="btn btn-spin" style="margin-top: 20px;" onclick="applyPromo()">FAOL LASHTIRISH</button>
        <button class="btn" style="background: transparent; color: #666;" onclick="closeModals()">Yopish</button>
    </div>
</div>

<script>
    // --- ADMIN SOZLAMALARI ---
    const GLOBAL_PROMO = "UZB777"; // Sizning promokodingiz
    const PROMO_BONUS = 50;        // Bonus miqdori
    // -------------------------

    let angle = 0;
    const SPIN_LIMIT = 3;
    const DAY_MS = 24 * 60 * 60 * 1000;

    let storage = JSON.parse(localStorage.getItem('uc_app_v1')) || {
        balance: 0, tries: SPIN_LIMIT, lastTime: 0, promoUsed: false
    };

    function updateView() {
        document.getElementById('balance-num').innerText = storage.balance;
        document.getElementById('spin-btn').innerText = `AYLANTIRISH (${storage.tries}/${SPIN_LIMIT})`;
        checkTime();
    }

    function checkTime() {
        const now = Date.now();
        if (storage.tries <= 0) {
            const diff = now - storage.lastTime;
            if (diff >= DAY_MS) {
                storage.tries = SPIN_LIMIT;
                save();
                location.reload();
            } else {
                document.getElementById('spin-btn').disabled = true;
                document.getElementById('timer').style.display = 'block';
                startTimer(DAY_MS - diff);
            }
        }
    }

    function startTimer(ms) {
        const span = document.getElementById('countdown');
        const timer = setInterval(() => {
            ms -= 1000;
            if (ms <= 0) { clearInterval(timer); location.reload(); }
            let h = Math.floor(ms / 3600000);
            let m = Math.floor((ms % 3600000) / 60000);
            let s = Math.floor((ms % 60000) / 1000);
            span.innerText = `${h.toString().padStart(2,'0')}:${m.toString().padStart(2,'0')}:${s.toString().padStart(2,'0')}`;
        }, 1000);
    }

    function spinWheel() {
        if (storage.tries <= 0) return;
        
        storage.tries--;
        if (storage.tries === 0) storage.lastTime = Date.now();
        save();
        
        const btn = document.getElementById('spin-btn');
        const wheel = document.getElementById('wheel');
        btn.disabled = true;
        
        const randomDeg = Math.floor(Math.random() * 360);
        angle += 1440 + randomDeg;
        wheel.style.transform = `rotate(${angle}deg)`;

        setTimeout(() => {
            const prizes = [10, 60, 0, 100, 20, 5];
            const won = prizes[Math.floor(Math.random() * prizes.length)];
            
            storage.balance += won;
            save();
            updateView();
            
            const msg = document.getElementById('status-msg');
            msg.innerText = won > 0 ? `TABRIKLAYMIZ: +${won} UC!` : "OMAD KELMADI, YANA URINIB KO'RING";
            msg.style.color = won > 0 ? "#2ecc71" : "#e74c3c";
            
            if (storage.tries > 0) btn.disabled = false;
        }, 4000);
    }

    function openWithdraw() {
        if (storage.balance < 360) {
            alert(`Sizga kamida 360 UC kerak. Hozirgi balans: ${storage.balance}`);
        } else {
            document.getElementById('withdraw-modal').style.display = 'flex';
        }
    }

    function openPromo() { document.getElementById('promo-modal').style.display = 'flex'; }
    function closeModals() { 
        document.getElementById('withdraw-modal').style.display = 'none';
        document.getElementById('promo-modal').style.display = 'none';
    }

    function finishWithdraw() {
        const id = document.getElementById('player-id').value;
        if (id.length < 5) return alert("ID xato kiritildi!");
        
        alert(`MUVAFFAQIYATLI!\nID: ${id}\nSizning hisobingizga ${storage.balance} UC yuborildi.`);
        storage.balance = 0;
        save();
        location.reload();
    }

    function applyPromo() {
        const input = document.getElementById('promo-input').value;
        if (storage.promoUsed) return alert("Siz promokoddan foydalangansiz!");
        
        if (input === GLOBAL_PROMO) {
            storage.balance += PROMO_BONUS;
            storage.promoUsed = true;
            save();
            alert(`TABRIKLAYMIZ! +${PROMO_BONUS} UC qo'shildi.`);
            location.reload();
        } else {
            alert("Promokod xato!");
        }
    }

    function save() { localStorage.setItem('uc_app_v1', JSON.stringify(storage)); }
    updateView();
</script>

</body>
</html>
