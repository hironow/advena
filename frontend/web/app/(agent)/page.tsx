'use client';

import dynamic from 'next/dynamic';
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

// SSRオフで D3 を使う
const LedVisualizer = dynamic(
  () => import('@/components/visualizer/LedVisualizer'),
  { ssr: false },
);

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
  const currentRadioShow = radioShows.find((rs) => rs.id === showRadioShowId);
  const audioPublicUrl = currentRadioShow?.audio_url;

  return (
    <>
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
          {currentRadioShow && (
            <>
              <BooksDisplayModal radioShow={currentRadioShow} />
              <ScriptDisplayModal radioShow={currentRadioShow} />
            </>
          )}
          <div className="flex flex-col gap-2">
            <BgmController src="/assets/bgm/bgm1.mp3" />
          </div>
          <div className="flex flex-col gap-2">
            {audioPublicUrl && <CustomAudioController src={audioPublicUrl} />}
          </div>
        </div>

        <div className="w-full flex justify-center items-center">
          <div className="fixed bottom-2 p-2">
            <LedVisualizer radioShow={currentRadioShow} />
          </div>
        </div>
      </div>
    </>
  );
}
