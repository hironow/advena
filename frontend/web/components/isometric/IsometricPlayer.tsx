'use client';

import React, { useEffect, useRef } from 'react';
import { keysDown } from './keyInput';
import { initTouchListeners, getTouchVector } from './touchInput';
import { getTilePosition, WORLD_SIZE } from './tileset';
import { useRafLoop } from '../../hooks/use-ref-loop';

const tileSpeed = 2.0; // 1秒に2マス進む想定 (調整OK)

export default function IsometricPlayer() {
  const tileXRef = useRef<number>(WORLD_SIZE - 2);
  const tileYRef = useRef<number>(WORLD_SIZE - 2);
  const layerRef = useRef<number>(0); // 高さレイヤー

  const playerDivRef = useRef<HTMLDivElement | null>(null);

  // キー + タッチ入力を元にプレイヤーの位置更新
  useRafLoop((deltaMs) => {
    const dt = deltaMs / 1000;

    // --- 1) PCキー入力（WASD）をベクトル化 ---
    let vxKey = 0;
    let vyKey = 0;
    if (keysDown.w) vyKey -= 1;
    if (keysDown.s) vyKey += 1;
    if (keysDown.a) vxKey -= 1;
    if (keysDown.d) vxKey += 1;

    const lenKey = Math.sqrt(vxKey * vxKey + vyKey * vyKey);
    if (lenKey > 0) {
      vxKey /= lenKey;
      vyKey /= lenKey;
    }

    // --- 2) タッチ入力をベクトル化 ( -1〜1 程度 ) ---
    const { vx: vxTouch, vy: vyTouch } = getTouchVector(80);

    // --- 3) 合成: どちらかが非ゼロなら合算 or どちらを優先するかを決める ---
    //    簡易的に 合成 してみる。実際には「タッチ入力があればそっち優先」など好きに調整OK
    let vx = vxKey + vxTouch;
    let vy = vyKey + vyTouch;
    const len = Math.sqrt(vx * vx + vy * vy);
    if (len > 1) {
      vx /= len;
      vy /= len;
    }

    // --- 4) タイル座標を移動 ---
    tileXRef.current += vx * tileSpeed * dt;
    tileYRef.current += vy * tileSpeed * dt;

    // クリップ
    tileXRef.current = Math.max(0, Math.min(WORLD_SIZE - 1, tileXRef.current));
    tileYRef.current = Math.max(0, Math.min(WORLD_SIZE - 1, tileYRef.current));

    // --- 5) タイル座標 -> ピクセル座標に変換 ---
    const xInt = Math.floor(tileXRef.current);
    const yInt = Math.floor(tileYRef.current);
    const fracX = tileXRef.current - xInt;
    const fracY = tileYRef.current - yInt;

    const basePos = getTilePosition(xInt, yInt, layerRef.current);
    const plus1X = getTilePosition(xInt + 1, yInt, layerRef.current);
    const plus1Y = getTilePosition(xInt, yInt + 1, layerRef.current);

    const dxX = plus1X.pxX - basePos.pxX;
    const dxY = plus1X.pxY - basePos.pxY;
    const dyX = plus1Y.pxX - basePos.pxX;
    const dyY = plus1Y.pxY - basePos.pxY;

    const finalPxX = basePos.pxX + dxX * fracX + dyX * fracY;
    const finalPxY = basePos.pxY + dxY * fracX + dyY * fracY;

    // --- 6) DOM スタイル反映 ---
    if (playerDivRef.current) {
      playerDivRef.current.style.left = `${finalPxX}px`;
      playerDivRef.current.style.top = `${finalPxY}px`;
    }
  });

  // マウント時にタッチイベントを仕込む
  useEffect(() => {
    // 画面全体 or 親要素にタッチリスナを付ける想定
    // ここでは document.body に付けてみる (好みに応じて調整)
    const cleanup = initTouchListeners(document.body);

    // プレイヤーの初期スタイル
    if (playerDivRef.current) {
      playerDivRef.current.style.position = 'absolute';
      playerDivRef.current.style.width = '40px';
      playerDivRef.current.style.height = '40px';
      playerDivRef.current.style.backgroundColor = 'red';
      playerDivRef.current.style.zIndex = '999';
      playerDivRef.current.style.transform = 'translate(50%,100%)';
    }

    return () => {
      // アンマウント時のクリーンアップ (タッチリスナ解除)
      if (cleanup) cleanup();
    };
  }, []);

  return <div ref={playerDivRef} />;
}
