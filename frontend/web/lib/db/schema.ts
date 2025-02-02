// export const user = pgTable('User', {
//   id: uuid('id').primaryKey().notNull().defaultRandom(),
//   email: varchar('email', { length: 64 }).notNull(),
//   password: varchar('password', { length: 64 }),
// });

// export type User = InferSelectModel<typeof user>;
export type User = {
  id: string;
  email: string;
  password: string;
};

// export const chat = pgTable('Chat', {
//   id: uuid('id').primaryKey().notNull().defaultRandom(),
//   createdAt: timestamp('createdAt').notNull(),
//   title: text('title').notNull(),
//   userId: uuid('userId')
//     .notNull()
//     .references(() => user.id),
//   visibility: varchar('visibility', { enum: ['public', 'private'] })
//     .notNull()
//     .default('private'),
// });

// export type Chat = InferSelectModel<typeof chat>;
export type Chat = {
  id: string;
  createdAt: Date;
  title: string;
  userId: string;
  visibility: 'public' | 'private';
};

// export const message = pgTable('Message', {
//   id: uuid('id').primaryKey().notNull().defaultRandom(),
//   chatId: uuid('chatId')
//     .notNull()
//     .references(() => chat.id),
//   role: varchar('role').notNull(),
//   content: json('content').notNull(),
//   createdAt: timestamp('createdAt').notNull(),
// });

// export type Message = InferSelectModel<typeof message>;
export type Message = {
  id: string;
  chatId: string;
  role: string;
  content: any;
  createdAt: Date;
};

// export const vote = pgTable(
//   'Vote',
//   {
//     chatId: uuid('chatId')
//       .notNull()
//       .references(() => chat.id),
//     messageId: uuid('messageId')
//       .notNull()
//       .references(() => message.id),
//     isUpvoted: boolean('isUpvoted').notNull(),
//   },
//   (table) => {
//     return {
//       pk: primaryKey({ columns: [table.chatId, table.messageId] }),
//     };
//   },
// );

// export type Vote = InferSelectModel<typeof vote>;
export type Vote = {
  chatId: string;
  messageId: string;
  isUpvoted: boolean;
};

// export const document = pgTable(
//   'Document',
//   {
//     id: uuid('id').notNull().defaultRandom(),
//     createdAt: timestamp('createdAt').notNull(),
//     title: text('title').notNull(),
//     content: text('content'),
//     kind: varchar('text', { enum: ['text', 'code'] })
//       .notNull()
//       .default('text'),
//     userId: uuid('userId')
//       .notNull()
//       .references(() => user.id),
//   },
//   (table) => {
//     return {
//       pk: primaryKey({ columns: [table.id, table.createdAt] }),
//     };
//   },
// );

// export type Document = InferSelectModel<typeof document>;
export type Document = {
  id: string;
  createdAt: Date;
  title: string;
  content: string;
  kind: 'text' | 'code';
  userId: string;
};

// export const suggestion = pgTable(
//   'Suggestion',
//   {
//     id: uuid('id').notNull().defaultRandom(),
//     documentId: uuid('documentId').notNull(),
//     documentCreatedAt: timestamp('documentCreatedAt').notNull(),
//     originalText: text('originalText').notNull(),
//     suggestedText: text('suggestedText').notNull(),
//     description: text('description'),
//     isResolved: boolean('isResolved').notNull().default(false),
//     userId: uuid('userId')
//       .notNull()
//       .references(() => user.id),
//     createdAt: timestamp('createdAt').notNull(),
//   },
//   (table) => ({
//     pk: primaryKey({ columns: [table.id] }),
//     documentRef: foreignKey({
//       columns: [table.documentId, table.documentCreatedAt],
//       foreignColumns: [document.id, document.createdAt],
//     }),
//   }),
// );

// export type Suggestion = InferSelectModel<typeof suggestion>;
export type Suggestion = {
  id: string;
  documentId: string;
  documentCreatedAt: Date;
  originalText: string;
  suggestedText: string;
  description: string;
  isResolved: boolean;
  userId: string;
  createdAt: Date;
};
