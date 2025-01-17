'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Book, generateBooks } from './book';
import { BookCover } from './BookCover';
import styles from './shelf.module.css';

export function RotatingBookshelf() {
  const [books] = useState<Book[]>(() => generateBooks(15));
  const [centerIndex, setCenterIndex] = useState(Math.floor(books.length / 2));
  const containerRef = useRef<HTMLDivElement>(null);

  // スクロールが止まったら自動的に近い本にスナップ
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    let rafId: number;
    let isScrolling: NodeJS.Timeout | null = null;

    const handleScroll = () => {
      // スクロール中は cancelAnimationFrame / requestAnimationFrame で調整
      cancelAnimationFrame(rafId);
      rafId = requestAnimationFrame(() => {
        // 現在のスクロール量からインデックスを計算
        const scrollPosition = container.scrollLeft;
        const newCenterIndex = Math.round(scrollPosition / 120);
        if (newCenterIndex !== centerIndex) {
          setCenterIndex(newCenterIndex);
        }
      });

      // スクロールが止まったタイミングでスナップ
      if (isScrolling) clearTimeout(isScrolling);
      isScrolling = setTimeout(() => {
        const newCenterIndex = Math.round(container.scrollLeft / 120);
        scrollToIndex(newCenterIndex);
      }, 200); // 200ms程度待機してからスナップ
    };

    container.addEventListener('scroll', handleScroll, { passive: true });
    return () => {
      container.removeEventListener('scroll', handleScroll);
      cancelAnimationFrame(rafId);
      if (isScrolling) {
        clearTimeout(isScrolling);
      }
    };
  }, [centerIndex]);

  // 任意のインデックスへスムーススクロールする関数
  const scrollToIndex = useCallback((index: number) => {
    const container = containerRef.current;
    if (!container) return;
    // 1冊あたりの横幅 120px を利用
    container.scrollTo({
      left: index * 120,
      behavior: 'smooth',
    });
    setCenterIndex(index);
  }, []);

  // BookCover をクリックした時に呼ばれるハンドラ
  const handleSelectBook = (index: number) => {
    scrollToIndex(index);
  };

  return (
    <div className={styles.bookshelf}>
      <div className={styles.shelfInner}>
        <div
          ref={containerRef}
          style={{
            // 横スクロール時のスナップ設定
            scrollSnapType: 'x mandatory',
          }}
        >
          <div
            className="flex items-center"
            style={{
              width: `${books.length * 120}px`,
              transformStyle: 'preserve-3d',
              overflow: 'scroll',
              // backfaceVisibility: 'hidden',
            }}
          >
            {books.map((book, index) => (
              <div
                key={book.id}
                className="flex-none"
                // 子要素ごとにスナップの基準を設定
                style={{
                  scrollSnapAlign: 'center',
                }}
              >
                <BookCover
                  book={book}
                  index={index}
                  centerIndex={centerIndex}
                  totalBooks={books.length}
                  onSelect={handleSelectBook}
                />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
