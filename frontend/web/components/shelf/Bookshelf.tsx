'use client';

import React, { memo, useCallback } from 'react';
import type {
  RadioShow,
  RadioShowBook,
} from '@/lib/firestore/generated/entity_radio_show';
import Image from 'next/image';

interface BookCoverProps {
  book: RadioShowBook;
  onSelect: (book: RadioShowBook) => void;
}

function BookCoverComponent({ book, onSelect }: BookCoverProps) {
  return (
    <div
      onClick={() => onSelect(book)}
      className="cursor-pointer transition-transform duration-200 hover:scale-105"
    >
      <Image
        src={book.thumbnail_url}
        alt={book.title}
        width={150} // 必要に応じてサイズを調整
        height={220} // 必要に応じてサイズを調整
        className="object-cover rounded-md"
      />
      <p className="mt-2 text-center text-sm font-medium text-gray-800">
        {book.title}
      </p>
    </div>
  );
}

export const BookCover = memo(BookCoverComponent);

export function Bookshelf({ radioShow }: { radioShow?: RadioShow }) {
  const books = radioShow?.books || [];

  const handleSelectBook = useCallback((book: RadioShowBook) => {
    console.log('Selected book:', book.url);
    // 必要に応じて外部リンクへの遷移処理などを追加
  }, []);

  return (
    // sticky で画面上部に固定（固定しない場合はクラスを削除してください）
    <div className="sticky top-0 bg-white z-10 overflow-x-auto">
      <div className="flex space-x-4 px-4 py-2">
        {books.map((book) => (
          <div key={book.url} className="flex-shrink-0">
            <BookCover book={book} onSelect={handleSelectBook} />
          </div>
        ))}
      </div>
    </div>
  );
}
