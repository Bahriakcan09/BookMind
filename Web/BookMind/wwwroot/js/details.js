document.addEventListener('DOMContentLoaded', () => {
    if (typeof BOOK_ID !== 'undefined') {
        loadBookDetails(BOOK_ID);
    }
});

const loadBookDetails = async (id) => {
    const container = document.getElementById('book-details-container');
    
    try {
        console.log("Firestore'dan kitap detayı çekiliyor:", id);
        // Firestore'dan tekil doküman çekme
        const doc = await db.collection('books').doc(id).get();
        
        if (!doc.exists) {
            throw new Error('Kitap bulunamadı');
        }

        const data = doc.data();
        // Embedding alanını ayıkla
        const { embedding, ...book } = data;
        
        renderDetails(book);
    } catch (error) {
        console.error('Error fetching details from Firestore:', error);
        container.innerHTML = `
            <div class="alert alert-danger mt-5">
                <h4>Hata!</h4>
                <p>Kitap bilgileri yüklenirken bir sorun oluştu.</p>
                <a href="/" class="btn btn-primary">Ana Sayfaya Dön</a>
            </div>
        `;
    }
};

const renderDetails = (book) => {
    const container = document.getElementById('book-details-container');
    const noCover = 'https://via.placeholder.com/400x600?text=No+Cover';
    // Firestore'daki alan adı cover_url (snake_case)
    const originalCover = book.cover_url ? book.cover_url.replace('http://', 'https://') : noCover;
    const highResCover = originalCover.includes('google.com') ? originalCover.replace('zoom=1', 'zoom=2') : originalCover;

    container.innerHTML = `
        <nav aria-label="breadcrumb" class="mb-4">
            <ol class="breadcrumb">
                <li class="breadcrumb-item"><a href="/">Ana Sayfa</a></li>
                <li class="breadcrumb-item active" aria-current="page">${book.title}</li>
            </ol>
        </nav>

        <div class="row">
            <div class="col-md-4 mb-4">
                <div class="card border-0 shadow-sm overflow-hidden">
                    <img src="${highResCover}" 
                         onerror="if(this.src !== '${originalCover}') { this.src='${originalCover}'; } else { this.src='${noCover}'; }"
                         class="img-fluid" 
                         alt="${book.title}" 
                         style="width: 100%; height: auto;">
                </div>
            </div>
            <div class="col-md-8">
                <div class="ps-md-4">
                    <h1 class="display-6 fw-bold mb-2">${book.title}</h1>
                    <h4 class="text-muted mb-4">${book.author}</h4>
                    
                    <div class="d-flex align-items-center mb-4">
                        <span class="badge bg-primary me-2 px-3 py-2">${book.genre}</span>
                        <span class="text-muted small">ISBN: ${book.isbn || 'N/A'}</span>
                    </div>

                    <div class="card border-0 bg-light p-4 mb-4">
                        <h5 class="fw-bold mb-3">Kitap Hakkında</h5>
                        <p class="text-secondary lh-lg" style="text-align: justify;">
                            ${book.description || 'Bu kitap için henüz bir açıklama girilmemiş.'}
                        </p>
                    </div>

                    <div class="d-flex align-items-center justify-content-between border-top pt-4">
                        <div>
                            <span class="text-muted d-block small">Fiyat</span>
                            <h2 class="text-primary fw-bold mb-0">${book.price} ₺</h2>
                        </div>
                        <button class="btn btn-primary btn-lg px-5 shadow-sm" id="add-to-cart-detail">
                            <i class="bi bi-cart-plus me-2"></i> Sepete Ekle
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

    document.getElementById('add-to-cart-detail').addEventListener('click', () => {
        window.addToCart(book.id, book.title, book.price, originalCover);
    });
};
