// Sepet verisini başlat
let cart = JSON.parse(localStorage.getItem('bookmind_cart')) || [];
let firebaseListenerRef = null;

// Firebase'e veri yazma (Sadece yerel değişiklik olduğunda çağrılır)
const syncToFirebase = async () => {
    if (typeof auth === 'undefined' || typeof rtdb === 'undefined') return;
    const user = auth.currentUser;
    if (user) {
        try {
            // Dinleyiciyi geçici olarak devre dışı bırakmaya gerek yok çünkü set() işlemi
            // dinleyiciyi tetiklese bile gelen veri yerelle aynı olacağı için renderCart() masrafı az olur.
            await rtdb.ref(`carts/${user.uid}`).set(cart);
        } catch (error) {
            console.error("Firebase Sync Error:", error);
        }
    }
};

// Firebase'den anlık veri dinleme
const setupCartListener = (user) => {
    if (!user || typeof rtdb === 'undefined') return;

    // Eğer eski bir dinleyici varsa önce onu kapat
    if (firebaseListenerRef) {
        firebaseListenerRef.off();
    }

    firebaseListenerRef = rtdb.ref(`carts/${user.uid}`);
    firebaseListenerRef.on('value', (snapshot) => {
        const fbCart = snapshot.val();
        
        // Eğer DB boşsa (silinmişse) veya farklıysa yerel sepeti güncelle
        if (fbCart) {
            // Veri farklı mı kontrolü (basit JSON string karşılaştırması)
            if (JSON.stringify(fbCart) !== JSON.stringify(cart)) {
                cart = fbCart;
                localStorage.setItem('bookmind_cart', JSON.stringify(cart));
                if (typeof window.renderCart === 'function') window.renderCart();
            }
        } else if (cart.length > 0) {
            // DB'den veri silinmiş ama yerelde hala varsa temizle
            cart = [];
            localStorage.setItem('bookmind_cart', JSON.stringify(cart));
            if (typeof window.renderCart === 'function') window.renderCart();
        }
    });
};

// Auth değişikliklerini dinle
if (typeof auth !== 'undefined') {
    auth.onAuthStateChanged((user) => {
        if (user) {
            setupCartListener(user);
        } else {
            // Çıkış yapıldığında dinleyiciyi kapat
            if (firebaseListenerRef) {
                firebaseListenerRef.off();
                firebaseListenerRef = null;
            }
            // Çıkış yapınca sepeti temizleyelim mi yoksa yerelde kalsın mı? 
            // Genelde güvenlik için temizlenir ama localstorage'da kalması istenmişti.
        }
    });
}

window.addToCart = (id, title, price, coverUrl) => {
    const numPrice = Number(price);
    const existingItem = cart.find(item => item.id === id);
    
    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        cart.push({ 
            id: id, 
            title: title, 
            price: numPrice, 
            coverUrl: coverUrl, 
            quantity: 1 
        });
    }
    window.saveCart();
    alert(`"${title}" sepete eklendi!`);
    if (typeof window.renderCart === 'function') window.renderCart();
};

window.removeFromCart = (id) => {
    cart = cart.filter(item => item.id !== id);
    window.saveCart();
    if (typeof window.renderCart === 'function') window.renderCart();
};

window.updateQuantity = (id, delta) => {
    const item = cart.find(item => item.id === id);
    if (item) {
        item.quantity += delta;
        if (item.quantity <= 0) {
            window.removeFromCart(id);
        } else {
            window.saveCart();
            if (typeof window.renderCart === 'function') window.renderCart();
        }
    }
};

window.saveCart = () => {
    localStorage.setItem('bookmind_cart', JSON.stringify(cart));
    syncToFirebase(); 
};

window.completeOrder = async () => {
    if (cart.length === 0) return { success: false, message: "Sepetiniz boş." };

    const user = typeof auth !== 'undefined' ? auth.currentUser : null;
    const orderData = {
        items: [...cart],
        total: cart.reduce((sum, item) => sum + (item.price * item.quantity), 0),
        orderDate: new Date().toISOString(),
        orderId: 'ORD-' + Math.random().toString(36).substr(2, 9).toUpperCase()
    };

    if (user && typeof rtdb !== 'undefined') {
        try {
            // 1. Firebase'e siparişi ekle
            await rtdb.ref(`orders/${user.uid}`).push(orderData);
            
            // 2. Satın alınan kitapları kütüphaneye (Library) ekle
            const libraryRef = rtdb.ref(`libraries/${user.uid}`);
            for (const item of cart) {
                // Kütüphanede bu kitap zaten var mı kontrol edebiliriz ama 
                // şimdilik her satın almayı ekleyelim (farklı formatta olabilir)
                await libraryRef.push({
                    id: item.id,
                    title: item.title,
                    author: "Yazar Bilgisi", // Sepette yazar bilgisi yoksa varsayılan
                    coverUrl: item.coverUrl,
                    addedDate: new Date().toISOString(),
                    source: "purchase"
                });
            }

            // 3. Mevcut sepeti buluttan temizle
            await rtdb.ref(`carts/${user.uid}`).remove();
        } catch (error) {
            console.error("Firebase Order/Library Sync Error:", error);
        }
    }

    // Yerel veriyi temizle
    cart = [];
    localStorage.removeItem('bookmind_cart');
    return { success: true, orderId: orderData.orderId };
};

window.renderCart = () => {
    const cartItems = document.getElementById('cart-items');
    const cartTotal = document.getElementById('cart-total');
    const cartTotalFinal = document.getElementById('cart-total-final');
    if (!cartItems) return;

    if (cart.length === 0) {
        cartItems.innerHTML = '<div class="text-center p-5"><h4 class="text-muted">Sepetiniz boş.</h4><a href="/" class="btn btn-primary mt-3">Alışverişe Başla</a></div>';
        if (cartTotal) cartTotal.textContent = '0.00 ₺';
        if (cartTotalFinal) cartTotalFinal.textContent = '0.00 ₺';
        return;
    }

    let total = 0;
    cartItems.innerHTML = cart.map(item => {
        const itemPrice = Number(item.price);
        const itemTotal = itemPrice * item.quantity;
        total += itemTotal;
        
        return `
            <div class="card mb-3 border-0 shadow-sm">
                <div class="row g-0 align-items-center">
                    <div class="col-md-2 p-2 text-center">
                        <img src="${item.coverUrl}" class="img-fluid rounded" alt="${item.title}" style="max-height: 100px; object-fit: contain;">
                    </div>
                    <div class="col-md-5 p-3">
                        <h5 class="fw-bold mb-1">${item.title}</h5>
                        <p class="text-primary mb-0">${itemPrice.toFixed(2)} ₺</p>
                    </div>
                    <div class="col-md-3 p-3">
                        <div class="input-group input-group-sm" style="width: 100px;">
                            <button class="btn btn-outline-secondary" onclick="window.updateQuantity('${item.id}', -1)">-</button>
                            <span class="input-group-text bg-white border-secondary">${item.quantity}</span>
                            <button class="btn btn-outline-secondary" onclick="window.updateQuantity('${item.id}', 1)">+</button>
                        </div>
                    </div>
                    <div class="col-md-2 p-3 text-end">
                        <p class="fw-bold mb-1">${itemTotal.toFixed(2)} ₺</p>
                        <button class="btn btn-sm btn-link text-danger p-0" onclick="window.removeFromCart('${item.id}')">Kaldır</button>
                    </div>
                </div>
            </div>
        `;
    }).join('');

    const formattedTotal = `${total.toFixed(2)} ₺`;
    if (cartTotal) cartTotal.textContent = formattedTotal;
    if (cartTotalFinal) cartTotalFinal.textContent = formattedTotal;
};

document.addEventListener('DOMContentLoaded', () => {
    window.renderCart();
});
