export interface Book {
  id: string;
  title: string;
  author: string;
  coverUrl: string;
}

// シンプルにダミー本を返すサンプル
export function generateBooks(count: number): Book[] {
  const b = (v: number) => {
    // odd or even
    switch (v % 2) {
      case 0:
        return `/assets/book/dummy2.jpg`;
      case 1:
        return `/assets/book/dummy1.jpg`;
      default:
        return `/assets/book/dummy1.jpg`;
    }
  };

  return Array.from({ length: count }, (_, i) => ({
    id: `book-${i + 1}`,
    title: `タイトル ${i + 1}`,
    author: `作者 ${i + 1}`,
    coverUrl: b(i),
  }));
}
