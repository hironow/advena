'use client';

import dynamic from 'next/dynamic';

import IsometricWorld from '@/components/isometric/IsometricWorld';
import { useAudioContextState } from '@/components/visualizer/audio-context-provider';
import { Button } from '@/components/ui/button';
import { ChatHeader } from '@/components/chat-header';
import { useSession } from 'next-auth/react';
import { useAtomValue } from 'jotai';
import type { RadioShow } from '@/lib/firestore/generated/entity_radio_show';
import { currentRadioShowIdAtom, radioShowsAtom } from '@/lib/state';
import BgmController from '@/components/visualizer/BgmController';
import { ScriptDisplayModal } from '@/components/visualizer/ScriptDisplayModal';
import { BooksDisplayModal } from '@/components/visualizer/BooksDisplayModal';
import { toast } from 'sonner';

// SSRオフにしてD3を使う
const LedVisualizer = dynamic(
  () => import('@/components/visualizer/LedVisualizer'),
  { ssr: false },
);

const InitMicButton: React.FC = () => {
  const { data: session } = useSession();
  console.info('client component session: ', session);
  const { initAudio, micAllowed } = useAudioContextState();

  if (micAllowed) {
    return (
      <Button variant="ghost" className="text-blue-400">
        Mic is active. Speak up!
      </Button>
    );
  }

  return <Button onClick={initAudio}>Init Mic & Start Visualization</Button>;
};

export default function Page() {
  const showRadioShowId = useAtomValue<string | null>(currentRadioShowIdAtom);
  const radioShows = useAtomValue<RadioShow[]>(radioShowsAtom);

  const { audioCtx } = useAudioContextState();

  const currentRadioShow = radioShows.find((rs) => rs.id === showRadioShowId);
  const hasAudio = !!currentRadioShow?.audio_url;
  const audioPublicUrl = currentRadioShow?.audio_url;

  return (
    <div className="relative flex flex-col min-w-0 h-dvh bg-background">
      <ChatHeader />
      <IsometricWorld
        cb={(x, y) => {
          // (5,7): エレベーター
          // (7,5): お家
          if (x === 5 && y === 7) {
            toast('紹介された本も見れますよ！');
          } else if (x === 7 && y === 5) {
            toast('ラジオ番組の台本も読めますよ！');
          }
        }}
      />

      {/* 右側に固定したサイドバー */}
      <div className="fixed top-18 sm:top-18 right-6 flex flex-col gap-4 items-end">
        {currentRadioShow && (
          <>
            <BooksDisplayModal radioShow={currentRadioShow} />
            <ScriptDisplayModal radioShow={currentRadioShow} />
          </>
        )}
        <div className="flex flex-col gap-2">
          <InitMicButton />
          {hasAudio && audioPublicUrl && <BgmController src={audioPublicUrl} />}
        </div>
      </div>

      {/* LedVisualizer を右下に配置 */}
      <div className="w-full flex justify-center items-center">
        <div className="fixed bottom-2 p-2">
          <LedVisualizer radioShow={currentRadioShow} />
        </div>
      </div>
    </div>
  );
}
