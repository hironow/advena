'use client';

import React, { useState, useEffect } from 'react';
import styles from './isometric.module.css';
import IsometricBackground from './IsometricBackground';
import IsometricPlayer from './IsometricPlayer';
import IsometricCamera from './IsometricCamera';
import { initKeyListeners } from './keyInput';
import { WORLD_SIZE } from './tileset';
import { Label } from '../ui/label';

/**
 * 全体をまとめる "ワールド" コンポーネント
 * - 画面中央にプレイヤーを固定するために、IsometricCamera を利用
 * - カメラが毎フレーム「プレイヤー座標」を参照して動く
 */
export default function IsometricWorld() {
  // プレイヤーのスクリーン座標を state で保持
  // (これをカメラに渡して、中心に持ってくる)
  const [playerPos, setPlayerPos] = useState({ x: 0, y: 0 });

  // プレイヤーの描画座標更新を受け取る
  const handlePlayerPosUpdate = (x: number, y: number) => {
    setPlayerPos({ x: x, y: y });
  };

  return (
    <div className={styles.isometricGame}>
      {/* gameInner: カメラ含む全体。overflowを使い画面サイズを固定して表示 */}
      <div className={styles.gameInner}>
        {/*
          IsometricCamera にプレイヤー座標を渡す
          children に 背景 + プレイヤー を入れる
        */}
        <Label>
          player = ({playerPos.x}, {playerPos.y})
        </Label>
        <IsometricCamera
          containerWidth={800} // 同じ値をCSS側の .isometricGame width と合わせる
          containerHeight={600} // 同じ値をCSS側の .isometricGame height と合わせる
          getPlayerScreenPos={() => ({
            x: playerPos.x,
            y: playerPos.y,
          })}
        >
          {/* 背景 */}
          <IsometricBackground />

          {/* プレイヤー */}
          <IsometricPlayer onUpdatePos={handlePlayerPosUpdate} />
        </IsometricCamera>
      </div>
    </div>
  );
}
