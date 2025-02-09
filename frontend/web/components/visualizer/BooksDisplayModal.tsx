'use client';

import { useState, useEffect } from 'react';
import type { FC } from 'react';
import type { RadioShow } from '@/lib/firestore/generated/entity_radio_show';

import { Button } from '../ui/button';
import { CrossIcon } from '../icons';
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
  // テキスト内容の状態管理
  const [content, setContent] = useState<string>('');
  // エラー状態
  const [error, setError] = useState<string>('');

  // モーダルを開く処理
  const openModal = () => setIsOpen(true);
  // モーダルを閉じる処理（状態のリセットを含む）
  const closeModal = () => {
    setIsOpen(false);
    setContent('');
    setError('');
  };

  const books = radioShow.books;
  const booksDisplay = books?.map((book) => {
    return (
      <div key={book.url} className="flex items-center gap-2">
        <div>{book.title}</div>
        {/* 外部リンク 別たぶで開く */}
        <Link href={book.url} target="_blank" rel="noopener noreferrer">
          <LinkIcon />
        </Link>
        <div>{book.isbn !== '' ? book.isbn : book.jp_e_code}</div>
      </div>
    );
  });

  return (
    <>
      {/* モーダルを開くボタン */}
      <Button onClick={openModal}>Show Books</Button>

      {isOpen && (
        // モーダル全体のラッパー（画面全体を覆う）
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          {/* 背景のオーバーレイ。クリックでモーダルを閉じる */}
          <div
            className="absolute inset-0 bg-black opacity-50"
            onClick={closeModal}
          />
          {/* モーダル本体 */}
          <Card className="relative z-10 w-full max-w-xl p-6 overflow-auto max-h-[80vh]">
            <div className="flex justify-end">
              <Button variant="ghost" onClick={closeModal}>
                <CrossIcon />
              </Button>
            </div>
            <div>
              {error && <p className="text-red-500">エラー: {error}</p>}
              {!error && (
                // <pre> タグで改行や空白もそのまま表示
                <div
                  className="whitespace-pre-wrap"
                  style={{
                    fontFamily: dotGothic16.style.fontFamily,
                  }}
                >
                  {booksDisplay}
                </div>
              )}
            </div>
          </Card>
        </div>
      )}
    </>
  );
};
