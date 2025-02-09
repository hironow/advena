import { atom } from 'jotai';
import type { User } from '@/lib/firestore/generated/entity_user';
import type { RadioShow } from '@/lib/firestore/generated/entity_radio_show';
// import { Message, Note, Notebook, Source } from '@/lib/firebase/firestore';

// const sidebarOpenAtom = atom(true);
// const showChatModalAtom = atom(false);
// const chatMessagesAtom = atom<Message[]>([]);
// const sourcesAtom = atom<Source[]>([]);
// const notesAtom = atom<Note[]>([]);
// const notebooksAtom = atom<Notebook[]>([]);
const currentRadioShowIdAtom = atom<string | null>(null);
const userAtom = atom<User | null>(null);
const radioShowsAtom = atom<RadioShow[]>([]);
// const messageAtom = atom('');
// const sourceAtom = atom<Source | null>(null);
// const commonQuestionsAtom = atom<string[]>((get) => {
//   const commonQuestions: string[] = [];
//   get(sourcesAtom).map((source) => {
//     if (source.selected && source.questions) {
//       commonQuestions.push(...source.questions);
//     }
//   });
//   return commonQuestions;
// });

export {
  //   chatMessagesAtom,
  //   commonQuestionsAtom,
  //   messageAtom,
  //   notebooksAtom,
  //   notesAtom,
  //   showChatModalAtom,
  //   sidebarOpenAtom,
  //   sourceAtom,
  //   sourcesAtom,
  userAtom,
  radioShowsAtom,
  currentRadioShowIdAtom,
};
