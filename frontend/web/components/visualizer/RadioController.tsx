import { useRef, useState } from 'react';
import { Button } from '@/components/ui/button';
import { PauseIcon, RadioTowerIcon } from 'lucide-react';

const CustomAudioController: React.FC<{ src: string }> = ({ src }) => {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  const togglePlayback = async () => {
    if (!audioRef.current) return;

    if (isPlaying) {
      // 再生中なら一時停止する
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      // 再生していなければ再生する
      try {
        await audioRef.current.play();
        setIsPlaying(true);
      } catch (error) {
        console.error('Audio playback error:', error);
      }
    }
  };

  return (
    <div>
      {/* crossOrigin 属性を付与して CORS 対策 */}
      <audio ref={audioRef} crossOrigin="anonymous" src={src} hidden />
      <Button onClick={togglePlayback}>
        {isPlaying ? <PauseIcon /> : <RadioTowerIcon />}
      </Button>
    </div>
  );
};

export default CustomAudioController;
