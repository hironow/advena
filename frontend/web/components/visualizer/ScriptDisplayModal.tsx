'use client';

import { useState } from 'react';
import type { FC } from 'react';
import type { RadioShow } from '@/lib/firestore/generated/entity_radio_show';

import { ScriptDisplay } from './ScriptDisplay';
import { Button } from '../ui/button';
import { CrossIcon, LogsIcon } from '../icons';
import { Card } from '../ui/card';

interface ScriptDisplayModalProps {
  radioShow: RadioShow;
}

export const ScriptDisplayModal: FC<ScriptDisplayModalProps> = ({
  radioShow,
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const openModal = () => setIsOpen(true);
  const closeModal = () => setIsOpen(false);

  return (
    <>
      {/* モーダルを開くためのボタン */}
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
            onKeyUp={(e) => {
              if (e.key === 'Escape') closeModal();
            }}
            tabIndex={0}
            role="button"
            aria-label="Close modal"
          />
          {/* モーダル本体 */}
          <Card className="relative z-10 w-full max-w-xl p-6">
            {/* モーダル内の閉じるボタン */}
            <div className="flex justify-end">
              <Button variant="ghost" onClick={closeModal}>
                <CrossIcon />
              </Button>
            </div>
            {/* ScriptDisplay の内容をモーダル内に表示 */}
            <ScriptDisplay radioShow={radioShow} />
          </Card>
        </div>
      )}
    </>
  );
};
