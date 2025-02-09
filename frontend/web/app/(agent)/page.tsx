'use client';

import dynamic from 'next/dynamic';

import IsometricWorld from '@/components/isometric/IsometricWorld';

import { useAudioContextState } from '@/components/visualizer/audio-context-provider';
import { Button } from '@/components/ui/button';
import { ChatHeader } from '@/components/chat-header';
import { useSession } from 'next-auth/react';

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
  return (
    <>
      <div className="flex flex-col min-w-0 h-dvh bg-background">
        <ChatHeader />

        <IsometricWorld />
        <div>
          {/* footerで固定したエリアに再生系と可視化系を積み上げる */}
          <LedVisualizer />
        </div>
      </div>
    </>
  );
}
