'use client';

import React, { memo, useState, useRef, useEffect, useCallback } from 'react';
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
    <>
      <Image src={book.thumbnail_url} alt={book.title} className="" />
      <div className="">
        <p className="">{book.title}</p>
      </div>
    </>
  );
}

// 余計な再レンダリングを防ぐために React.memo でラップ
export const BookCover = memo(BookCoverComponent);

export function Bookshelf({ radioShow }: { radioShow: RadioShow | undefined }) {
  const books = radioShow?.books || [];

  const handleSelectBook = useCallback((book: RadioShowBook) => {
    // tapしたら外部に飛びますか？を出して遷移できる
    const book_public_url = book.url;
    console.log('Selected book:', book_public_url);
  }, []);

  return (
    <div className="">
      <div className="">
        {books.map((book, index) => (
          <div
            key={book.url}
            className="flex-none"
            // 子要素ごとにスナップの基準を設定
            style={{
              scrollSnapAlign: 'center',
            }}
          >
            <BookCover book={book} onSelect={handleSelectBook} />
          </div>
        ))}
      </div>
    </div>
  );
}
