'use client';

import { useState, useEffect } from 'react';
import type { FC } from 'react';
import type { RadioShow } from '@/lib/firestore/generated/entity_radio_show';

import { Button } from '../ui/button';
import { CrossIcon, LogsIcon } from '../icons';
import { Card } from '../ui/card';
import { DotGothic16 } from 'next/font/google';

const dotGothic16 = DotGothic16({
  weight: '400',
  subsets: ['latin'],
});

interface ScriptDisplayModalProps {
  radioShow: RadioShow;
}

export const ScriptDisplayModal: FC<ScriptDisplayModalProps> = ({
  radioShow,
}) => {
  // モーダルの開閉状態
  const [isOpen, setIsOpen] = useState(false);
  // テキスト内容の状態管理
  const [content, setContent] = useState<string>('');
  // 読み込み状態
  const [loading, setLoading] = useState(false);
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

  // モーダルが開いたら radioShow.script_public_url にリクエストしてテキストを取得する
  useEffect(() => {
    if (isOpen && radioShow?.script_url) {
      setLoading(true);
      fetch(radioShow.script_url)
        .then((response) => {
          if (!response.ok) {
            throw new Error(`HTTP error: ${response.statusText}`);
          }
          return response.text();
        })
        .then((text) => {
          setContent(text);
          setLoading(false);
        })
        .catch((err) => {
          setError(err.message);
          setLoading(false);
        });
    }
  }, [isOpen, radioShow]);

  return (
    <>
      {/* モーダルを開くボタン */}
      <Button onClick={openModal}>
        <LogsIcon />
      </Button>

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
            <div className="flex justify-between items-center mb-4">
              <h2 className={`text-xl font-bold ${dotGothic16.className}`}>
                Script
              </h2>
              <Button variant="ghost" onClick={closeModal}>
                <CrossIcon />
              </Button>
            </div>
            <div>
              {loading && <p>読み込み中...</p>}
              {error && <p className="text-red-500">エラー: {error}</p>}
              {!loading && !error && (
                // <pre> タグで改行や空白もそのまま表示
                <pre
                  className="whitespace-pre-wrap"
                  style={{
                    fontFamily: dotGothic16.style.fontFamily,
                  }}
                >
                  {content}
                </pre>
              )}
            </div>
          </Card>
        </div>
      )}
    </>
  );
};
