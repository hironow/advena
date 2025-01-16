'use client';

import React, { useState, useEffect } from 'react';
import styles from './IsometricWorld.module.css';
import IsometricBackground from './IsometricBackground';

import Tile from './FrogIcon';
import { clock1, START_X, START_Y, WORLD_SIZE } from './tileset';
import IsometricPlayer from './IsometricPlayer';

interface IPlayer {
  x: number;
  y: number;
  dir: 'up' | 'down' | 'left' | 'right';
  dead: boolean;
}

export default function IsometricWorld() {
  const [frog, setFrog] = useState<IPlayer>({
    x: START_X,
    y: START_Y,
    dir: 'up',
    dead: false,
  });

  // --- キー操作 ---
  // useEffect(() => {
  //   const onKeyDown = (e: KeyboardEvent) => {
  //     let next = { ...frog };
  //     const minXorY = 0;
  //     const maxXorY = WORLD_SIZE - 1;

  //     switch (e.key) {
  //       case 'ArrowLeft':
  //         next.x = frog.x - 1;
  //         next.y = frog.y + 1;
  //         next.dir = 'left';
  //         break;
  //       case 'ArrowRight':
  //         next.x = frog.x + 1;
  //         next.y = frog.y - 1;
  //         next.dir = 'right';
  //         break;
  //       case 'ArrowUp':
  //         next.x = frog.x - 1;
  //         next.y = frog.y - 1;
  //         next.dir = 'up';
  //         break;
  //       case 'ArrowDown':
  //         next.x = frog.x + 1;
  //         next.y = frog.y + 1;
  //         next.dir = 'down';
  //         break;
  //       default:
  //         return;
  //     }

  //     // TODO: mapに応じて行ける範囲がレイヤーで決まる、右端にいけない
  //     // 範囲外にいってしまうのは避ける
  //     if (
  //       next.x < minXorY ||
  //       next.x > maxXorY ||
  //       next.y < minXorY ||
  //       next.y > maxXorY
  //     ) {
  //       return;
  //     }
  //     console.info('next', next);
  //     setFrog(next);
  //   };
  //   window.addEventListener('keydown', onKeyDown);
  //   return () => window.removeEventListener('keydown', onKeyDown);
  // }, [frog]);

  return (
    <div className={styles.isometricGame}>
      <div className={styles.gameInner}>
        <IsometricBackground className={styles.backgroundContainer} />
        <IsometricPlayer />

        <PlayerOnTile x={frog.x} y={frog.y} dir={frog.dir} />
      </div>
    </div>
  );
}

/** Player描画用 */
function PlayerOnTile(props: {
  x: number;
  y: number;
  dir: 'up' | 'down' | 'left' | 'right';
}) {
  const [reverse, setReverse] = useState(false);
  const [prevDir, setPrevDir] = useState<'up' | 'down' | 'left' | 'right'>(
    'up',
  );

  // 左右反転時にreverseを切り替える
  useEffect(() => {
    if (props.dir === 'left') {
      setReverse(true);
    } else {
      setReverse(false);
    }
  }, [props.dir]);

  return (
    <div className={styles.frogContainer}>
      <Tile tile={clock1} x={props.x} y={props.y} layer={0} reverse={reverse} />
    </div>
  );
}
