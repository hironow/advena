'use client';

import React, { useState } from 'react';
import styles from './isometric.module.css';
import IsometricBackground from './IsometricBackground';
import IsometricPlayer from './IsometricPlayer';
import IsometricCamera from './IsometricCamera';
import { Label } from '../ui/label';
import { dummy_layer_map } from './tileset';

/**
 * 全体をまとめる "ワールド" コンポーネント
 */
export default function IsometricWorld() {
  // プレイヤーのタイル座標:
  // 頂上が (0, 0) で、真下が (WORLD_SIZE-1, WORLD_SIZE-1) となる
  const initialPlayerPos = { x: 0, y: 0, layer: dummy_layer_map[0][0] };
  const [playerPos, setPlayerPos] =
    useState<typeof initialPlayerPos>(initialPlayerPos);

  // プレイヤーのタイル座標更新を受け取る (描画のpx座標ではない)
  const handlePlayerPosUpdate = (x: number, y: number, layer: number) => {
    if (playerPos.x !== x || playerPos.y !== y || playerPos.layer !== layer) {
      // 更新頻度を抑える
      setPlayerPos({ x: x, y: y, layer: layer });
    }
  };

  return (
    <div className={styles.isometricGame}>
      {/* overflowは .isometricGame が隠している */}
      <div className={styles.gameInner}>
        {/* カメラ外は座標系が統一されていない前提 */}
        <Label>
          player = ({playerPos.x}, {playerPos.y}, {playerPos.layer})
        </Label>

        {/* カメラ内は座標系が統一されている前提 */}
        <IsometricCamera
          // CSS側の .isometricGame width, height と一致させる
          containerWidth={800}
          containerHeight={600}
          // プレイヤーの画面座標を取得するコールバック
          getPlayerScreenPos={() => ({
            x: playerPos.x,
            y: playerPos.y,
            layer: playerPos.layer,
          })}
        >
          <IsometricBackground />
          <IsometricPlayer
            initialPos={initialPlayerPos}
            onUpdatePos={handlePlayerPosUpdate}
          />
        </IsometricCamera>
      </div>
    </div>
  );
}
