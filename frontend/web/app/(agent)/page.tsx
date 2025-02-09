'use client';

import dynamic from 'next/dynamic';

import IsometricWorld from '@/components/isometric/IsometricWorld';

import { useAudioContextState } from '@/components/visualizer/audio-context-provider';
import { Button } from '@/components/ui/button';
import { ChatHeader } from '@/components/chat-header';
import { useSession } from 'next-auth/react';
import { Bookshelf } from '@/components/shelf/Bookshelf';
import { useAtomValue } from 'jotai';
import type { RadioShow } from '@/lib/firestore/generated/entity_radio_show';
import { currentRadioShowIdAtom, radioShowsAtom } from '@/lib/state';
import BgmController from '@/components/visualizer/BgmController';
import { Card } from '@/components/ui/card';
import {
  ScriptDisplay,
  ScriptDisplayModal,
} from '@/components/visualizer/ScriptDisplayModal';
import { BooksDisplayModal } from '@/components/visualizer/BooksDisplayModal';

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
    <>
      <div className="flex flex-col min-w-0 h-dvh bg-background">
        <ChatHeader />
        <div>
          {/* TODO: 本が横一連に並んでいるUI */}
          {/* <Bookshelf radioShow={currentRadioShow} /> */}
          {currentRadioShow && (
            <BooksDisplayModal radioShow={currentRadioShow} />
          )}
        </div>

        <IsometricWorld />

        {/* script表示をModalとして実装 */}
        <div className="fixed left-6 rounded-xl p-6 flex flex-col gap-8 leading-relaxed text-center max-w-xl mx-auto">
          {currentRadioShow && (
            <ScriptDisplayModal radioShow={currentRadioShow} />
          )}
        </div>

        {/* controller 右に整列 */}
        <div className="w-full flex justify-center items-center">
          <div className="fixed top-6 right-3 p-2">
            <InitMicButton />
            {hasAudio && audioPublicUrl && (
              <BgmController src={audioPublicUrl} />
            )}
          </div>
        </div>

        {/* 可視化は中央真下に浮かせる */}
        <div className="w-full flex justify-center items-center">
          <div className="fixed bottom-2 p-2">
            <LedVisualizer radioShow={currentRadioShow} />
          </div>
        </div>
      </div>
    </>
  );
}
