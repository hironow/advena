'use client';

import { ChatHeader } from '@/components/chat-header';
import { useAtomValue } from 'jotai';
import type { RadioShow } from '@/lib/firestore/generated/entity_radio_show';
import { currentRadioShowIdAtom, radioShowsAtom } from '@/lib/state';
import BgmController from '@/components/visualizer/BgmController';
import { ScriptDisplayModal } from '@/components/visualizer/ScriptDisplayModal';
import { BooksDisplayModal } from '@/components/visualizer/BooksDisplayModal';
import { toast } from 'sonner';
import { AudioProvider } from '@/components/visualizer/audio-context-provider';
import IsometricWorld from '@/components/isometric/IsometricWorld';
import CustomAudioController from '@/components/visualizer/RadioController';

const bgms = ['/assets/bgm/bgm1.mp3', '/assets/bgm/bgm2.mp3'];

// ページ全体を AudioProvider でラップする
export default function Page() {
  return (
    <AudioProvider>
      <PageContent />
    </AudioProvider>
  );
}

function PageContent() {
  const showRadioShowId = useAtomValue<string | null>(currentRadioShowIdAtom);
  const radioShows = useAtomValue<RadioShow[]>(radioShowsAtom);

  // 現在のラジオ番組を変数に保持
  const currentRadioShow = radioShows.find((rs) => rs.id === showRadioShowId);
  // 現在のラジオ番組の音声URLを取得
  const audioPublicUrl = currentRadioShow?.audio_url;

  // BGMをランダムに選択
  const bgm = bgms[Math.floor(Math.random() * bgms.length)];

  return (
    <div className="relative flex flex-col min-w-0 h-dvh bg-background">
        <ChatHeader />

        <IsometricWorld
          cb={(x, y) => {
            // (1,0): メモリアル
            // (5,7): エレベーター
            // (7,5): お家
            if (x === 5 && y === 7) {
              toast('紹介された本も見れますよ！');
            } else if (x === 7 && y === 5) {
              toast('ラジオ番組の台本も読めますよ！');
            } else if (x === 1 && y === 0) {
              toast('ミ=ホはまだ beta version です🥺');
            }
          }}
        />

        <div className="fixed top-18 right-6 flex flex-col gap-4 items-end">
          <div className="flex flex-col gap-2">
            <BgmController src={bgm} />
          </div>
          {currentRadioShow && (
            <>
              <BooksDisplayModal radioShow={currentRadioShow} />
              <ScriptDisplayModal radioShow={currentRadioShow} />
            </>
          )}
          <div className="flex flex-col gap-2">
            {currentRadioShow && audioPublicUrl && (
              <CustomAudioController src={audioPublicUrl} />
            )}
          </div>
        </div>
      </div>
  );
}
