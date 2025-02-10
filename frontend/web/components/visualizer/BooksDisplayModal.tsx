'use client';

import { useState, useRef } from 'react';
import type { FC } from 'react';
import type { RadioShow } from '@/lib/firestore/generated/entity_radio_show';

import { Button } from '../ui/button';
import { CrossIcon, GlobeIcon } from '../icons';
import { Card } from '../ui/card';
import { DotGothic16 } from 'next/font/google';
import Link from 'next/link';
import { LinkIcon, ArrowUp, ArrowDown } from 'lucide-react';

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
  // スクロール可能な領域への ref を作成
  const cardRef = useRef<HTMLDivElement>(null);

  const openModal = () => setIsOpen(true);
  const closeModal = () => setIsOpen(false);

  // 上にスクロールする処理（例：300pxずつ上に移動）
  const scrollUp = () => {
    if (cardRef.current) {
      cardRef.current.scrollBy({ top: -300, behavior: 'smooth' });
    }
  };

  // 下にスクロールする処理（例：300pxずつ下に移動）
  const scrollDown = () => {
    if (cardRef.current) {
      cardRef.current.scrollBy({ top: 300, behavior: 'smooth' });
    }
  };

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

          {/* モーダル本体とスクロールボタンを内包するコンテナ */}
          <div className="relative">
            {/* 上方向のスクロールボタン：モーダルの直上に配置 */}
            <div className="absolute -top-8 left-1/2 transform -translate-x-1/2">
              <Button onClick={scrollUp} className="rounded-full p-2">
                <ArrowUp className="w-5 h-5" />
              </Button>
            </div>

            {/* スクロール可能なモーダルコンテンツ */}
            <Card
              ref={cardRef}
              className="w-full max-w-xl p-6 overflow-y-auto max-h-[80vh]"
              style={{ WebkitOverflowScrolling: 'touch' }}
            >
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
                style={{ fontFamily: dotGothic16.style.fontFamily }}
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
                  <li>書籍はありません</li>
                )}
              </ul>
            </Card>

            {/* 下方向のスクロールボタン：モーダルの直下に配置 */}
            <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2">
              <Button onClick={scrollDown} className="rounded-full p-2">
                <ArrowDown className="w-5 h-5" />
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
