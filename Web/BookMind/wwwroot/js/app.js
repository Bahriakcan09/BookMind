let allBooks = [];
let filteredBooks = [];
let currentPage = 1;
const itemsPerPage = 20;

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('book-list')) {
        init();
    }
});

const init = async () => {
    await loadBooks();
    setupFilters();
};

const loadBooks = async () => {
    const bookList = document.getElementById('book-list');
    if (!bookList) return;
    
    bookList.innerHTML = '<div class="col-12 text-center p-5"><div class="spinner-border text-primary" role="status"></div></div>';

    try {
        // API yerine Firestore'dan çekiyoruz
        console.log("Firestore'dan kitaplar çekiliyor...");
        const snapshot = await db.collection('books').get();
        
        allBooks = snapshot.docs.map(doc => {
            const data = doc.data();
            // Embedding alanını bellekten tasarruf için çıkarıyoruz
            const { embedding, ...bookWithoutEmbedding } = data;
            return bookWithoutEmbedding;
        });

        filteredBooks = [...allBooks];
        console.log("Firestore'dan veri çekildi. Toplam kitap:", allBooks.length);
        
        renderGenres();
        window.renderPage(1);
    } catch (error) {
        console.error('Error loading books from Firestore:', error);
        bookList.innerHTML = '<div class="alert alert-danger">Kitaplar yüklenirken bir hata oluştu. Lütfen Firebase bağlantınızı kontrol edin.</div>';
    }
};

const renderGenres = () => {
    const genreContainer = document.getElementById('genre-filters');
    if (!genreContainer) return;

    const allGenres = allBooks.flatMap(b => b.genre ? b.genre.split(',').map(g => g.trim()) : []);
    const uniqueGenres = ['all', ...new Set(allGenres)].sort((a, b) => a === 'all' ? -1 : a.localeCompare(b));
    
    genreContainer.innerHTML = uniqueGenres.map(genre => `
        <button class="list-group-item list-group-item-action ${genre === 'all' ? 'active' : ''}" 
                data-genre="${genre}">
            ${genre === 'all' ? 'Tüm Kitaplar' : genre}
        </button>
    `).join('');

    genreContainer.querySelectorAll('button').forEach(btn => {
        btn.addEventListener('click', (e) => {
            genreContainer.querySelector('.active').classList.remove('active');
            e.currentTarget.classList.add('active');
            filterByGenre(e.currentTarget.dataset.genre);
        });
    });
};

const setupFilters = () => {
    const searchInput = document.getElementById('search-input');
    if (!searchInput) return;

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        filteredBooks = allBooks.filter(b => 
            (b.title && b.title.toLowerCase().includes(query)) || 
            (b.author && b.author.toLowerCase().includes(query))
        );
        currentPage = 1;
        window.renderPage(1);
    });
};

const filterByGenre = (genre) => {
    if (genre === 'all') {
        filteredBooks = [...allBooks];
    } else {
        filteredBooks = allBooks.filter(b => b.genre && b.genre.split(',').map(g => g.trim()).includes(genre));
    }
    currentPage = 1;
    window.renderPage(1);
};

// Global fonksiyon olarak ata
window.renderPage = (page) => {
    currentPage = page;
    const bookList = document.getElementById('book-list');
    if (!bookList) return;

    const start = (page - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    const pageBooks = filteredBooks.slice(start, end);
    
    const noCover = 'https://via.placeholder.com/250x400?text=No+Cover';

    bookList.innerHTML = pageBooks.map(book => {
        const originalCover = book.cover_url ? book.cover_url.replace('http://', 'https://') : noCover;
        const highResCover = originalCover.includes('google.com') ? originalCover.replace('zoom=1', 'zoom=2') : originalCover;
        
        return `
        <div class="col-md-3 mb-4">
            <div class="card h-100 border-0 shadow-sm book-card" onclick="location.href='/Home/Details/${book.id}'" style="cursor: pointer;">
                <img src="${highResCover}" 
                     onerror="if(this.src !== '${originalCover}') { this.src='${originalCover}'; } else { this.src='${noCover}'; }"
                     class="card-img-top" 
                     alt="${book.title}" 
                     style="height: 350px; object-fit: cover;">
                <div class="card-body d-flex flex-column">
                    <h5 class="card-title fw-bold text-truncate" title="${book.title}">${book.title}</h5>
                    <p class="card-text text-muted small mb-2">${book.author}</p>
                    <div class="mt-auto d-flex justify-content-between align-items-center">
                        <span class="fw-bold text-primary">${book.price} ₺</span>
                        <button class="btn btn-sm btn-outline-primary px-3 add-to-cart-btn" 
                                data-id="${book.id}" 
                                data-title="${book.title.replace(/"/g, '&quot;')}" 
                                data-price="${book.price}" 
                                data-cover="${originalCover}"
                                onclick="event.stopPropagation();">
                            <i class="bi bi-cart-plus"></i> Sepete Ekle
                        </button>
                    </div>
                </div>
            </div>
        </div>
        `;
    }).join('');

    document.querySelectorAll('.add-to-cart-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const d = e.currentTarget.dataset;
            window.addToCart(d.id, d.title, d.price, d.cover);
        });
    });

    renderPagination();
    window.scrollTo(0, 0);
};

const renderPagination = () => {
    const pagination = document.getElementById('pagination');
    if (!pagination) return;

    const totalPages = Math.ceil(filteredBooks.length / itemsPerPage);
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }

    let buttons = '';
    buttons += `<li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
        <a class="page-link" href="javascript:void(0)" onclick="window.renderPage(1)">&#171;&#171;</a>
    </li>`;

    buttons += `<li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
        <a class="page-link" href="javascript:void(0)" onclick="window.renderPage(${currentPage - 1})">&#60;</a>
    </li>`;

    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, startPage + 4);
    if (endPage - startPage < 4) startPage = Math.max(1, totalPages - 4);
    if (startPage < 1) startPage = 1;

    for (let i = startPage; i <= endPage; i++) {
        buttons += `<li class="page-item ${i === currentPage ? 'active' : ''}">
            <a class="page-link" href="javascript:void(0)" onclick="window.renderPage(${i})">${i}</a>
        </li>`;
    }

    buttons += `<li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
        <a class="page-link" href="javascript:void(0)" onclick="window.renderPage(${currentPage + 1})">&#62;</a>
    </li>`;

    buttons += `<li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
        <a class="page-link" href="javascript:void(0)" onclick="window.renderPage(${totalPages})">&#187;&#187;</a>
    </li>`;

    pagination.innerHTML = buttons;
};
