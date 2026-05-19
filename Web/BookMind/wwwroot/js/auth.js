document.addEventListener('DOMContentLoaded', () => {
    const navAuthLinks = document.getElementById('nav-auth-links');

    // Update UI based on auth state
    auth.onAuthStateChanged((user) => {
        if (user) {
            // User is signed in
            navAuthLinks.innerHTML = `
                <li class="nav-item dropdown">
                    <a class="nav-link dropdown-toggle text-dark" href="#" id="navbarDropdown" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                        ${user.email}
                    </a>
                    <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="navbarDropdown">
                        <li><a class="dropdown-item" href="/Cart">Sepetim</a></li>
                        <li><a class="dropdown-item" href="/Cart/Orders">Siparişlerim</a></li>
                        <li><a class="dropdown-item" href="/Library">Kütüphanem</a></li>
                        <li><hr class="dropdown-divider"></li>
                        <li><a class="dropdown-item text-danger" href="#" id="btn-logout">Çıkış Yap</a></li>
                    </ul>
                </li>
            `;
            
            document.getElementById('btn-logout').addEventListener('click', (e) => {
                e.preventDefault();
                auth.signOut().then(() => {
                    window.location.href = '/';
                });
            });
        } else {
            // User is signed out
            navAuthLinks.innerHTML = `
                <li class="nav-item">
                    <a class="nav-link text-dark" href="/Auth/Login">Giriş Yap</a>
                </li>
                <li class="nav-item">
                    <a class="nav-link btn btn-outline-primary ms-2" href="/Auth/Register">Kayıt Ol</a>
                </li>
            `;
        }
    });
});

// Helper for Auth Pages
const handleAuth = (type, email, password) => {
    if (type === 'register') {
        return auth.createUserWithEmailAndPassword(email, password);
    } else {
        return auth.signInWithEmailAndPassword(email, password);
    }
};
