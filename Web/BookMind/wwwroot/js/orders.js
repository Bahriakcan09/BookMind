document.addEventListener('DOMContentLoaded', () => {
    auth.onAuthStateChanged((user) => {
        if (user) {
            loadOrders(user.uid);
        } else {
            window.location.href = '/Auth/Login';
        }
    });
});

const loadOrders = (uid) => {
    const container = document.getElementById('orders-container');
    
    rtdb.ref(`orders/${uid}`).on('value', (snapshot) => {
        const orders = snapshot.val();
        
        if (!orders) {
            container.innerHTML = `
                <div class="card border-0 shadow-sm p-5 text-center">
                    <i class="bi bi-bag-x text-muted mb-3" style="font-size: 3rem;"></i>
                    <h4 class="text-muted">Henüz hiç siparişiniz bulunmuyor.</h4>
                    <div class="mt-3">
                        <a href="/" class="btn btn-primary">Kitaplara Göz At</a>
                    </div>
                </div>
            `;
            return;
        }

        // Objeden diziye çevir ve tarihe göre ters sırala (en yeni en üstte)
        const orderList = Object.keys(orders).map(key => ({
            ...orders[key],
            key: key
        })).sort((a, b) => new Date(b.orderDate) - new Date(a.orderDate));

        renderOrders(orderList);
    });
};

const renderOrders = (orders) => {
    const container = document.getElementById('orders-container');
    
    container.innerHTML = orders.map(order => `
        <div class="card border-0 shadow-sm mb-4 overflow-hidden">
            <div class="card-header bg-light py-3 border-0">
                <div class="row align-items-center">
                    <div class="col-md-3">
                        <span class="text-muted small d-block">SİPARİŞ TARİHİ</span>
                        <span class="fw-bold">${new Date(order.orderDate).toLocaleDateString('tr-TR')}</span>
                    </div>
                    <div class="col-md-3">
                        <span class="text-muted small d-block">TOPLAM</span>
                        <span class="fw-bold text-primary">${order.total.toFixed(2)} ₺</span>
                    </div>
                    <div class="col-md-3">
                        <span class="text-muted small d-block">SİPARİŞ NO</span>
                        <span class="fw-bold text-secondary">#${order.orderId}</span>
                    </div>
                    <div class="col-md-3 text-end">
                        <span class="badge bg-success">Hazırlanıyor</span>
                    </div>
                </div>
            </div>
            <div class="card-body">
                <div class="row">
                    ${order.items.map(item => `
                        <div class="col-md-6 mb-3">
                            <div class="d-flex align-items-center">
                                <img src="${item.coverUrl}" class="rounded shadow-sm" style="width: 50px; height: 75px; object-fit: cover;">
                                <div class="ms-3">
                                    <h6 class="mb-0 fw-bold">${item.title}</h6>
                                    <p class="mb-0 text-muted small">${item.quantity} Adet x ${item.price} ₺</p>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `).join('');
};
