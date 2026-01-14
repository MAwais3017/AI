import { initializeApp } from 'firebase/app';
import { getAuth, initializeAuth, getReactNativePersistence } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyCacsDjvqEmxzVWw_wHseN7S-W7WGAVYrw",
  authDomain: "med-ai-b497f.firebaseapp.com",
  projectId: "med-ai-b497f",
  storageBucket: "med-ai-b497f.firebasestorage.app",
  messagingSenderId: "591182698180",
  appId: "1:591182698180:web:c61984c0f064b827439b91"
};

let app;
try {
  app = initializeApp(firebaseConfig);
  console.log('Firebase initialized successfully');
} catch (error) {
  console.error('Error initializing Firebase:', error);
  throw error;
}

let auth;
try {
  auth = initializeAuth(app, {
    persistence: getReactNativePersistence(AsyncStorage)
  });
  console.log('Firebase Auth initialized successfully');
} catch (error) {
  console.log('Auth already initialized, getting existing instance');
  auth = getAuth(app);
}

let db;
try {
  db = getFirestore(app);
  console.log('Firestore initialized successfully');
} catch (error) {
  console.error('Error initializing Firestore:', error);
  throw error;
}

export { auth, db };
export default app;

