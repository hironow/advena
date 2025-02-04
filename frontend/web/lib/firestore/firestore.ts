// clientから参照される firestore access library
// firebase packageのfirestoreを利用しているが、firebase-admin packageのfirestoreは利用しないこと

import { getFirestore, connectFirestoreEmulator } from 'firebase/firestore';
