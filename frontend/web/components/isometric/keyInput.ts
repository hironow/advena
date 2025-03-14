import { consoleLogWithStyle } from './utils';

// keyInput.ts
export const keysDown = {
  w: false,
  a: false,
  s: false,
  d: false,
};

export function initKeyListeners() {
  const handleKeyDown = (e: KeyboardEvent) => {
    switch (e.key.toLowerCase()) {
      case 'w':
        keysDown.w = true;
        break;
      case 'a':
        keysDown.a = true;
        break;
      case 's':
        keysDown.s = true;
        break;
      case 'd':
        keysDown.d = true;
        break;
    }
  };

  const handleKeyUp = (e: KeyboardEvent) => {
    switch (e.key.toLowerCase()) {
      case 'w':
        keysDown.w = false;
        break;
      case 'a':
        keysDown.a = false;
        break;
      case 's':
        keysDown.s = false;
        break;
      case 'd':
        keysDown.d = false;
        break;
    }
  };

  window.addEventListener('keydown', handleKeyDown);
  window.addEventListener('keyup', handleKeyUp);

  consoleLogWithStyle('%cisometric%c KeyInput listeners initialized');

  // アンマウント時に削除するなら
  return () => {
    window.removeEventListener('keydown', handleKeyDown);
    window.removeEventListener('keyup', handleKeyUp);
  };
}
