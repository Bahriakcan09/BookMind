// TODO: Replace with your project's Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyD728r3bSyZx9S0OicejL4AynSSRFhNq28",
    authDomain: "hackatonproject-b067e.firebaseapp.com",
    projectId: "hackatonproject-b067e",
    storageBucket: "hackatonproject-b067e.firebasestorage.app",
    messagingSenderId: "1003232788160",
    appId: "1:1003232788160:web:9655d966c345ed0856f725"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();
const rtdb = firebase.database();
const db = firebase.firestore();