export interface Book {
  id: string;
  title: string;
  author: string;
  coverUrl: string;
}

// シンプルにダミー本を返すサンプル
export function generateBooks(count: number): Book[] {
  return Array.from({ length: count }, (_, i) => ({
    id: `book-${i + 1}`,
    title: `タイトル ${i + 1}`,
    author: `作者 ${i + 1}`,
    coverUrl: '/assets/book/dummy.jpg',
  }));
}
