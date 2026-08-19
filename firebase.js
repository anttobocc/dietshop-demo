import { initializeApp } from "https://www.gstatic.com/firebasejs/12.14.0/firebase-app.js";
import {
  getFirestore,
  collection,
  getDocs,
  addDoc,
  updateDoc,
  deleteDoc,
  doc,
} from "https://www.gstatic.com/firebasejs/12.14.0/firebase-firestore.js";
import {
  getAuth,
  signInWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
} from "https://www.gstatic.com/firebasejs/12.14.0/firebase-auth.js";

const firebaseConfig = {
  apiKey: "AIzaSyDTkWXEpTmYIjOt63dlnKfkhfZqSwFI8vY",
  authDomain: "grandiet-demo.firebaseapp.com",
  projectId: "grandiet-demo",
  storageBucket: "grandiet-demo.firebasestorage.app",
  messagingSenderId: "51552961086",
  appId: "1:51552961086:web:99d6035587208b109f476f",
};

const app = initializeApp(firebaseConfig);
const db = getFirestore(app);
const auth = getAuth(app);

export {
  db, auth,
  collection, getDocs, addDoc, updateDoc, deleteDoc, doc,
  signInWithEmailAndPassword, signOut, onAuthStateChanged,
};
