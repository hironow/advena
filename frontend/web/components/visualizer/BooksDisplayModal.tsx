'use client';

import { useState } from 'react';
import type { FC } from 'react';
import type { RadioShow } from '@/lib/firestore/generated/entity_radio_show';

import { Button } from '../ui/button';
import { CrossIcon, GlobeIcon } from '../icons';
import { Card } from '../ui/card';
import { DotGothic16 } from 'next/font/google';
import Link from 'next/link';
import { LinkIcon } from 'lucide-react';

const dotGothic16 = DotGothic16({
  weight: '400',
  subsets: ['latin'],
});

interface BooksDisplayModalProps {
  radioShow: RadioShow;
}

export const BooksDisplayModal: FC<BooksDisplayModalProps> = ({
  radioShow,
}) => {
  // モーダルの開閉状態
  const [isOpen, setIsOpen] = useState(false);

  const openModal = () => setIsOpen(true);
  const closeModal = () => setIsOpen(false);

  // radioShow.books が存在しない場合にも対応
  const books = radioShow.books || [];

  return (
    <>
      {/* モーダルを開くボタン */}
      <Button onClick={openModal}>
        <GlobeIcon />
      </Button>

      {isOpen && (
        // 画面全体を覆うモーダルのラッパー
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          {/* 背景オーバーレイ：クリックでモーダルを閉じる */}
          <div
            className="absolute inset-0 bg-black opacity-50"
            onClick={closeModal}
          />
          {/* モーダル本体 */}
          <Card className="relative z-10 w-full max-w-xl p-6 overflow-y-auto max-h-[80vh]">
            {/* ヘッダー：タイトルと閉じるボタン */}
            <div className="flex justify-between items-center mb-4">
              <h2 className={`text-xl font-bold ${dotGothic16.className}`}>
                Books
              </h2>
              <Button variant="ghost" onClick={closeModal}>
                <CrossIcon />
              </Button>
            </div>
            {/* 本のリスト */}
            <ul
              className="flex flex-col gap-4"
              style={{
                fontFamily: dotGothic16.style.fontFamily,
              }}
            >
              {books.length > 0 ? (
                books.map((book) => (
                  <li key={book.url} className="flex flex-col border-b pb-2">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold">{book.title}</span>
                      {/* 外部リンク：新規タブで開く */}
                      <Link
                        href={book.url}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <LinkIcon className="w-5 h-5 text-blue-500" />
                      </Link>
                    </div>
                    <div className="text-sm text-gray-600">
                      {book.isbn !== ''
                        ? `ISBN: ${book.isbn}`
                        : `JP-eコード: ${book.jp_e_code}`}
                    </div>
                  </li>
                ))
              ) : (
                <li>No books available.</li>
              )}
            </ul>
          </Card>
        </div>
      )}
    </>
  );
};
