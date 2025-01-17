'use client';

import React, { useEffect, useRef } from 'react';
import { initKeyListeners, keysDown } from './keyInput';
import { initTouchListeners, getTouchVector } from './touchInput';
import {
  bird1,
  clock1,
  getLayerDiffY,
  getTilePosition,
  power1,
  WORLD_MAX_LAYER,
  WORLD_SIZE,
} from './tileset';
import { useRafLoop } from '../../hooks/use-ref-loop';
import Tile from './Tile';
import { consoleLogWithStyle } from './utils';
import styles from './isometric.module.css';

const tileSpeed = 2.5; // 1秒に2.5マス進む想定

interface IsometricPlayerProps {
  map: string[][];
  layerMap: number[][];
  className?: string;
  initialPos: { x: number; y: number; layer: number };
  centerFixed?: boolean;
  // 毎フレーム計算した「タイル座標」を親に通知するコールバック
  onUpdatePos?: (x: number, y: number, layer: number) => void;
}

export default function IsometricPlayer({
  map,
  layerMap,
  className,
  initialPos,
  onUpdatePos,
}: IsometricPlayerProps) {
  const tileXRef = useRef<number>(initialPos.x);
  const tileYRef = useRef<number>(initialPos.y);
  const layerRef = useRef<number>(initialPos.layer);

  const playerDivRef = useRef<HTMLDivElement | null>(null);

  const maxXorY = WORLD_SIZE - 1;
  const maxLayer = WORLD_MAX_LAYER - 1;
  const initialLayerDiffY = getLayerDiffY(initialPos.layer);

  useRafLoop((deltaMs) => {
    const dt = deltaMs / 1000;

    // 1) PCキー入力をベクトル化
    let vxKey = 0;
    let vyKey = 0;
    if (keysDown.w) vyKey -= 1;
    if (keysDown.s) vyKey += 1;
    if (keysDown.a) vxKey -= 1;
    if (keysDown.d) vxKey += 1;

    // 斜め移動の正規化
    const lenKey = Math.sqrt(vxKey * vxKey + vyKey * vyKey);
    if (lenKey > 0) {
      vxKey /= lenKey;
      vyKey /= lenKey;
    }

    // 2) タッチ入力をベクトル化
    const { vx: vxTouch, vy: vyTouch } = getTouchVector(80);

    // 3) 合成
    let vx = vxKey + vxTouch;
    let vy = vyKey + vyTouch;
    const len = Math.sqrt(vx * vx + vy * vy);
    if (len > 1) {
      vx /= len;
      vy /= len;
    }

    // 4) タイル座標を更新 (0 - WORLD_SIZE-1 でクリップ)
    tileXRef.current = Math.max(
      0,
      Math.min(maxXorY, tileXRef.current + vx * tileSpeed * dt),
    );
    tileYRef.current = Math.max(
      0,
      Math.min(maxXorY, tileYRef.current + vy * tileSpeed * dt),
    );

    // 5) タイル座標 -> ピクセル座標
    const xInt = Math.floor(tileXRef.current);
    const yInt = Math.floor(tileYRef.current);
    // レイヤーを更新 (0 - WORLD_MAX_LAYER-1 でクリップ)
    const layer = layerMap[xInt][yInt];
    layerRef.current = Math.max(0, Math.min(maxLayer, layer));

    const fracX = tileXRef.current - xInt;
    const fracY = tileYRef.current - yInt;

    const basePos = getTilePosition(xInt, yInt, layer);
    const plus1X = getTilePosition(xInt + 1, yInt, layer);
    const plus1Y = getTilePosition(xInt, yInt + 1, layer);

    const dxX = plus1X.pxX - basePos.pxX;
    const dxY = plus1X.pxY - basePos.pxY;
    const dyX = plus1Y.pxX - basePos.pxX;
    const dyY = plus1Y.pxY - basePos.pxY;

    const finalPxX = basePos.pxX + dxX * fracX + dyX * fracY;
    const finalPxY = basePos.pxY + dxY * fracX + dyY * fracY;

    // 6) DOM スタイル反映
    if (playerDivRef.current) {
      // transform で移動 (カメラにこの移動を逆転して渡したい、Reactの再レンダリングは避けること)
      // 初回描画時に0以外のレイヤーだった場合を考慮する。レイヤー0以外はマイナスの影響を受ける
      playerDivRef.current.style.transform = `translate(${finalPxX}px, ${finalPxY + initialLayerDiffY}px)`;

      // consoleLogWithStyle(
      //   `%cisometric%c Player is moved from (${xInt}, ${yInt}, ${layer}) to (${tileXRef.current}, ${tileYRef.current}, ${layerRef.current})`,
      // );
    }

    // 親にタイル座標を通知
    onUpdatePos?.(xInt, yInt, layer);
  });

  // 初回マウント時にイベント設定
  useEffect(() => {
    const keyCleanup = initKeyListeners();
    const touchCleanup = initTouchListeners(document.body);
    // TODO: clickした場所 (x,y) にプレイヤーを移動する機能もいる

    consoleLogWithStyle('%cisometric%c Player mounted in (0, 0)');
    return () => {
      if (keyCleanup) keyCleanup();
      if (touchCleanup) touchCleanup();
    };
  }, []);

  return (
    <div ref={playerDivRef} className={className}>
      <Tile
        tile={clock1}
        x={initialPos.x}
        y={initialPos.y}
        layer={initialPos.layer}
      />
    </div>
  );
}
