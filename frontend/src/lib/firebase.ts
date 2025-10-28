/**
 * Firebase Configuration and Initialization
 */
import { initializeApp, getApps, FirebaseApp } from 'firebase/app';
import { getAuth, Auth } from 'firebase/auth';
import { getFirestore, Firestore } from 'firebase/firestore';

const firebaseConfig = {
  apiKey: "AIzaSyD3jtsv2vNVym3pti_m8zdMJPF8py3RTGo",
  authDomain: "tarot-aacbf.firebaseapp.com",
  projectId: "tarot-aacbf",
  storageBucket: "tarot-aacbf.firebasestorage.app",
  messagingSenderId: "414870328191",
  appId: "1:414870328191:web:b5f81830d3657c609b804a",
  measurementId: "G-XBZDCBG5SQ"
};

// Initialize Firebase (singleton pattern)
let app: FirebaseApp;
let auth: Auth;
let db: Firestore;

if (typeof window !== 'undefined' && !getApps().length) {
  app = initializeApp(firebaseConfig);
  auth = getAuth(app);
  db = getFirestore(app);
} else if (typeof window !== 'undefined') {
  app = getApps()[0];
  auth = getAuth(app);
  db = getFirestore(app);
}

export { auth, db };
export default app;
