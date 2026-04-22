<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UC TERMINAL | Official</title>
    <style>
        /* Dizayn qismi */
        body { margin: 0; background: #0a0a0b; color: white; font-family: 'Segoe UI', sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .container { width: 90%; max-width: 350px; background: #151517; padding: 25px; border-radius: 25px; border: 1px solid #252525; text-align: center; box-shadow: 0 15px 35px rgba(0,0,0,0.5); }
        
        .balance-box { background: #1c1c1e; padding: 15px; border-radius: 15px; margin-bottom: 20px; }
        .balance-label { font-size: 12px; color: #888; text-transform: uppercase; }
        .balance-value { font-size: 38px; font-weight: bold; color: #f39c12; }

        /* Baraban stili */
        .wheel-container { position: relative; width: 220px; height: 220px; margin: 20px auto; border: 6px solid #222; border-radius: 50%; }
        #wheel { width: 100%; height: 100%; border-radius: 50%; transition: transform 4s cubic-bezier(0.15, 0, 0.15, 1);
            background: conic-gradient(#e74c3c 0% 16%, #3498db 16% 33%, #f1c40f 33% 50%, #2ecc71 50% 66%, #9b59b6 66% 83%, #e67e22 83% 100%);
        }
        .marker { position: absolute; top: -10px; left: 50%; transform: translateX(-50%); width: 0; height: 0; border-left: 12px solid transparent; border-right: 12px solid transparent; border-top: 22px solid #fff; z-index: 10; }

        /* Tugmalar */
        .btn { display: block; width: 100%; padding: 14px; margin: 10px 0; border-radius: 12px; border: none; font-weight: bold; font-size: 16px; cursor: pointer; transition: 0.3s; }
        .btn-spin { background: #fff; color: #000; }
        .btn-spin:disabled { background: #333; color: #666; }
        .btn-claim { background: #27ae60; color: white; }
        .btn-promo { background: transparent; border: 1px dashed #f39c12; color: #f39c12; font-size: 13px; }
        
        #msg { height: 20px; margin-top: 10px; font-size: 14px; font-weight: 500; }
    </style>
</head>
<body>

<div class="container">
    <h2 style="margin-top: 0;">UC TERMINAL</h2>
    
    <div class="balance-box">
        <div class="balance-label">Hisobingiz</div>
        <div class="balance-value"><span id="bal-val">0</span> UC</div>
    </div>

    <div class="wheel-container">
        <div class="marker"></div>
        <div id="wheel"></div>
    </div>

    <button class="btn btn-spin" id="spin-btn" onclick="startSpin()">AYLANTIRISH (3/3)</button>
    <button class="btn btn-claim" onclick="withdraw()">YECHIB OLISH</button>
    <button class="btn btn-promo" onclick="promoAction()">PROMOKOD KIRITISH</button>
    
    <div id="msg"></div>
</div>

<script>
    // Ma'lumotlarni saqlash
    let balance = parseInt(localStorage.getItem('uc_bal')) || 0;
    let tries = parseInt(localStorage.getItem('uc_tries')) || 3;
    let currentRotation = 0;

    // Ekranni yangilash
    function updateUI() {
        document.getElementById('bal-val').innerText = balance;
        document.getElementById('spin-btn').innerText = `AYLANTIRISH (${tries}/3)`;
        if(tries <= 0) document.getElementById('spin-btn').disabled = true;
    }

    // Aylantirish funksiyasi
    function startSpin() {
        if (tries <= 0) return;

        tries--;
        localStorage.setItem('uc_tries', tries);
        document.getElementById('spin-btn').disabled = true;
        
        const extraDeg = Math.floor(Math.random() * 360);
        currentRotation += 1800 + extraDeg; // 5 marta to'liq aylanadi
        document.getElementById('wheel').style.transform = `rotate(${currentRotation}deg)`;

        setTimeout(() => {
            const prizes = [10, 60, 0, 100, 20, 5];
            const won = prizes[Math.floor(Math.random() * prizes.length)];
            
            balance += won;
            localStorage.setItem('uc_bal', balance);
            
            const msgEl = document.getElementById('msg');
            msgEl.innerText = won > 0 ? `TABRIKLAYMIZ: +${won} UC!` : "BU SAFAR OMAD KELMADI";
            msgEl.style.color = won > 0 ? "#2ecc71" : "#e74c3c";
            
            updateUI();
            if (tries > 0) document.getElementById('spin-btn').disabled = false;
        }, 4000);
    }

    // Yechib olish
    function withdraw() {
        if (balance < 360) {
            alert("Minimal yechish 360 UC! Sizda: " + balance + " UC");
        } else {
            let id = prompt("PUBG ID raqamingizni kiriting:");
            if (id && id.length > 5) {
                alert("So'rov qabul qilindi! UC 24 soat ichida " + id + " raqamiga tushadi.");
                balance = 0;
                localStorage.setItem('uc_bal', 0);
                updateUI();
            } else {
                alert("ID xato!");
            }
        }
    }

    // Promokod (Admin uchun: UZB2026)
    function promoAction() {
        let p = prompt("Promokodni kiriting:");
        if (p === "UZB2026") {
            if (localStorage.getItem('promo_done')) {
                alert("Siz bu koddan foydalangansiz!");
            } else {
                balance += 50;
                localStorage.setItem('uc_bal', balance);
                localStorage.setItem('promo_done', 'true');
                alert("Muvaffaqiyatli! +50 UC qo'shildi.");
                updateUI();
            }
        } else {
            alert("Promokod xato!");
        }
    }

    updateUI();
</script>

</body>
</html>
