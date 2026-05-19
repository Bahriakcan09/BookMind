let html5QrCode = null;
let currentBook = null;
const GOOGLE_BOOKS_API_KEY = "AIzaSyAFvnL_1VocJWup7c7BZPMZ8KjpwOfvVJs";

document.addEventListener('DOMContentLoaded', () => {
    auth.onAuthStateChanged((user) => {
        if (user) {
            loadLibrary(user.uid);
        } else {
            window.location.href = '/Auth/Login';
        }
    });

    document.getElementById('btn-scan').addEventListener('click', toggleScanner);
    
    const fileInput = document.getElementById('barcode-file');
    document.getElementById('btn-upload').addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);

    document.getElementById('btn-isbn-add').addEventListener('click', () => {
        const query = document.getElementById('isbn-input').value.trim();
        if (query) fetchBookDetails(query);
    });

    document.getElementById('btn-confirm-add').addEventListener('click', saveBookToLibrary);
    
    // Manuel ekleme tetikleyicileri
    document.getElementById('btn-manual-form').addEventListener('click', () => {
        new bootstrap.Modal(document.getElementById('manualAddModal')).show();
    });

    document.getElementById('btn-manual-save').addEventListener('click', saveManualBook);
});

const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const btnUpload = document.getElementById('btn-upload');
    const originalHtml = btnUpload.innerHTML;
    btnUpload.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Analiz ediliyor...';

    if (!html5QrCode) {
        html5QrCode = new Html5Qrcode("reader");
    }

    // Görselden tarama yap (Hassasiyeti artırmak için ikinci parametreyi true tutuyoruz)
    html5QrCode.scanFile(file, true)
        .then(decodedText => {
            btnUpload.innerHTML = originalHtml;
            document.getElementById('detected-isbn').textContent = decodedText;
            document.getElementById('scan-result').classList.remove('d-none');
            fetchBookDetails(decodedText);
        })
        .catch(err => {
            btnUpload.innerHTML = originalHtml;
            console.error("Tarama hatası:", err);
            // Hata durumunda ISBN girişine odakla veya manuel girişi öner
            alert("Barkod net okunamadı. Lütfen altındaki ISBN numarasını (978...) manuel girin veya daha yakın bir fotoğraf çekin.");
            document.getElementById('isbn-input').focus();
        });
};

const toggleScanner = () => {
    if (!html5QrCode) {
        html5QrCode = new Html5Qrcode("reader", { 
            formatsToSupport: [ Html5QrcodeSupportedFormats.EAN_13, Html5QrcodeSupportedFormats.EAN_8 ]
        });
        
        const config = { fps: 20, qrbox: { width: 300, height: 180 } };
        
        html5QrCode.start({ facingMode: "environment" }, config, (decodedText) => {
            document.getElementById('detected-isbn').textContent = decodedText;
            document.getElementById('scan-result').classList.remove('d-none');
            fetchBookDetails(decodedText);
            stopScanner();
        }).catch(err => alert("Kamera başlatılamadı."));
        
        document.getElementById('btn-scan').innerHTML = '<i class="bi bi-stop-circle me-2"></i>Durdur';
    } else {
        stopScanner();
    }
};

const stopScanner = () => {
    if (html5QrCode) {
        html5QrCode.stop().then(() => {
            html5QrCode = null;
            document.getElementById('btn-scan').innerHTML = '<i class="bi bi-camera me-2"></i>Barkod Tara';
        });
    }
};

const fetchBookDetails = async (query) => {
    const isIsbn = /^\d+$/.test(query.replace(/\D/g, ''));
    const cleanQuery = isIsbn ? query.replace(/\D/g, '') : query;

    try {
        let url = `https://www.googleapis.com/books/v1/volumes?q=${isIsbn ? 'isbn:' : ''}${cleanQuery}&key=${GOOGLE_BOOKS_API_KEY}`;
        let response = await fetch(url);
        let data = await response.json();
        
        if (!data.items || data.totalItems === 0) {
            // Eğer ISBN ile bulunamadıysa (genel arama yap)
            url = `https://www.googleapis.com/books/v1/volumes?q=${cleanQuery}&key=${GOOGLE_BOOKS_API_KEY}`;
            response = await fetch(url);
            data = await response.json();
        }

        if (data.items && data.items.length > 0) {
            const info = data.items[0].volumeInfo;
            currentBook = {
                id: 'LIB-' + Date.now(),
                title: info.title || 'İsimsiz Kitap',
                author: info.authors ? info.authors.join(', ') : 'Bilinmeyen Yazar',
                coverUrl: info.imageLinks ? info.imageLinks.thumbnail.replace('http://', 'https://') : 'https://via.placeholder.com/150x200?text=No+Cover',
                genre: info.categories ? info.categories[0] : 'Edebiyat',
                description: info.description || '',
                isbn: isIsbn ? cleanQuery : (info.industryIdentifiers ? info.industryIdentifiers[0].identifier : '')
            };
            
            const modalBody = document.getElementById('modal-book-content');
            modalBody.innerHTML = `
                <img src="${currentBook.coverUrl}" class="rounded shadow mb-3" style="height: 150px;">
                <h5 class="fw-bold mb-1">${currentBook.title}</h5>
                <p class="text-muted small">${currentBook.author}</p>
            `;
            new bootstrap.Modal(document.getElementById('addBookModal')).show();
        } else {
            alert("Kitap bilgileri bulunamadı. Lütfen bilgileri manuel girmeyi deneyin.");
        }
    } catch (error) {
        console.error("API Error:", error);
    }
};

const saveBookToLibrary = async () => {
    const user = auth.currentUser;
    if (user && currentBook) {
        await rtdb.ref(`libraries/${user.uid}`).push(currentBook);
        bootstrap.Modal.getInstance(document.getElementById('addBookModal')).hide();
        currentBook = null;
        document.getElementById('isbn-input').value = '';
    }
};

const saveManualBook = async () => {
    const user = auth.currentUser;
    const title = document.getElementById('m-title').value.trim();
    const author = document.getElementById('m-author').value.trim();
    const cover = document.getElementById('m-cover').value.trim() || 'https://via.placeholder.com/150x200?text=No+Cover';

    if (user && title && author) {
        const book = {
            id: 'MAN-' + Date.now(),
            title: title,
            author: author,
            coverUrl: cover,
            genre: 'Manuel Kayıt',
            addedDate: new Date().toISOString()
        };
        await rtdb.ref(`libraries/${user.uid}`).push(book);
        bootstrap.Modal.getInstance(document.getElementById('manualAddModal')).hide();
        document.getElementById('manual-book-form').reset();
    } else {
        alert("Lütfen kitap adı ve yazar alanlarını doldurun.");
    }
};

const loadLibrary = (uid) => {
    rtdb.ref(`libraries/${uid}`).on('value', (snapshot) => {
        const books = snapshot.val();
        const container = document.getElementById('library-container');
        const countBadge = document.getElementById('library-count');
        
        if (!books) {
            container.innerHTML = '<div class="col-12 text-center p-5 text-muted">Kütüphaneniz boş.</div>';
            countBadge.textContent = "0 Kitap";
            return;
        }

        const bookList = Object.keys(books).map(key => ({ ...books[key], key: key }));
        countBadge.textContent = `${bookList.length} Kitap`;
        
        container.innerHTML = bookList.map(book => `
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="card h-100 border-0 shadow-sm overflow-hidden">
                    <div class="row g-0">
                        <div class="col-4">
                            <img src="${book.coverUrl}" class="img-fluid h-100" style="object-fit: cover; min-height: 120px;">
                        </div>
                        <div class="col-8 p-3">
                            <h6 class="fw-bold mb-1 text-truncate">${book.title}</h6>
                            <p class="text-muted small mb-2 text-truncate">${book.author}</p>
                            <button class="btn btn-sm btn-outline-danger" onclick="removeFromLibrary('${book.key}')">Sil</button>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    });
};

window.removeFromLibrary = async (key) => {
    if (confirm('Silmek istiyor musunuz?')) {
        const user = auth.currentUser;
        if (user) await rtdb.ref(`libraries/${user.uid}/${key}`).remove();
    }
};
