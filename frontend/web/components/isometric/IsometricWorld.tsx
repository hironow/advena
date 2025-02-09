'use client';

import React, { useEffect, useState } from 'react';
import styles from './isometric.module.css';
import IsometricBackground from './IsometricBackground';
import IsometricPlayer from './IsometricPlayer';
import IsometricCamera from './IsometricCamera';
import { dummy_layer_map, dummy_tile_map, zero_layer_map } from './tileset';
import { consoleLogWithStyle } from './utils';

// TODO: playerのポジションが変わった時だけに発火してcallbackする関数(modalの表示など)

interface IsometricWorldProps {
  cb: (x: number, y: number) => void;
}

/**
 * 全体をまとめる "ワールド" コンポーネント
 */
export default function IsometricWorld({ cb }: IsometricWorldProps) {
  // プレイヤーのタイル座標:
  // 頂上が (0, 0) で、真下が (WORLD_SIZE-1, WORLD_SIZE-1) となる
  const map = dummy_tile_map;
  const layerMap = zero_layer_map;

  const initialPlayerPos = { x: 0, y: 0, layer: layerMap[0][0] };
  const [playerPos, setPlayerPos] =
    useState<typeof initialPlayerPos>(initialPlayerPos);

  // プレイヤーのタイル座標更新を受け取る (描画のpx座標ではない)
  const handlePlayerPosUpdate = (x: number, y: number, layer: number) => {
    setPlayerPos({ x: x, y: y, layer: layer });
  };

  useEffect(() => {
    // プレイヤーのタイル座標が変わったらcallbackを実行する
    cb(playerPos.x, playerPos.y);
  }, [playerPos.x, playerPos.y]);

  return (
    <div className={styles.isometricGame}>
      {/* overflowは .isometricGame が隠している */}
      <div className={styles.gameInner}>
        {/* カメラ内は座標系が統一されている前提 */}
        <IsometricCamera
          // CSS側の .isometricGame width, height と一致させる
          containerWidth={800}
          containerHeight={600}
          // プレイヤーの画面座標を取得するコールバック TODO: 機能していない
          getPlayerScreenPos={() => ({
            x: playerPos.x,
            y: playerPos.y,
            layer: playerPos.layer,
          })}
          className={styles.camera}
        >
          <IsometricBackground
            map={map}
            layerMap={layerMap}
            className={styles.background}
          />
          <IsometricPlayer
            map={map}
            layerMap={layerMap}
            className={styles.player}
            initialPos={initialPlayerPos}
            onUpdatePos={handlePlayerPosUpdate}
          />
        </IsometricCamera>
      </div>
    </div>
  );
}
