'use client';

import React, { useRef } from 'react';
import { useRafLoop } from '../../hooks/use-ref-loop';

/**
 * 画面中央にプレイヤーを配置するための「カメラ」コンポーネント
 *
 * @param containerWidth  画面の幅(px)
 * @param containerHeight 画面の高さ(px)
 * @param getPlayerScreenPos プレイヤーの画面上座標を取得するコールバック
 */
export default function IsometricCamera({
  containerWidth = 1200,
  containerHeight = 600,
  getPlayerScreenPos,
  children,
}: {
  containerWidth: number;
  containerHeight: number;
  getPlayerScreenPos: () => { x: number; y: number };
  children: React.ReactNode;
}) {
  const worldRef = useRef<HTMLDivElement | null>(null);

  useRafLoop(() => {
    if (!worldRef.current) return;

    // 1) プレイヤーの描画上の座標を取得
    const { x, y } = getPlayerScreenPos();

    // 2) カメラオフセットを計算
    //    プレイヤーが画面中央(containerWidth/2, containerHeight/2)になるように
    const camOffsetX = -x + containerWidth / 2;
    const camOffsetY = -y + containerHeight / 2;

    // 3) transform で移動
    // worldRef.current.style.transform = `translate(${camOffsetX}px, ${camOffsetY}px)`;

    // console.info(
    //   '[isometric] Camera is moved to (',
    //   camOffsetX,
    //   ',',
    //   camOffsetY,
    //   ')',
    // );
  });

  return (
    <div
      // "world" 要素。ワールド(背景+プレイヤー等)全体をこの中に入れる
      ref={worldRef}
      style={{
        position: 'absolute',
        left: 0,
        top: 0,
        width: '600px', // マップ全体より大きめに確保
        height: '800px',
        backgroundColor: 'red',
      }}
    >
      {children}
    </div>
  );
}
