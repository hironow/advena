'use client';

import React, { useRef } from 'react';
import { useRafLoop } from '../../hooks/use-ref-loop';
import { getTilePosition } from './tileset';

interface IsometricCameraProps {
  className?: string;
  containerWidth: number;
  containerHeight: number;
  getPlayerScreenPos: () => { x: number; y: number; layer: number };
  children: React.ReactNode;
}

/**
 * 画面中央にプレイヤーを配置するための「カメラ」コンポーネント
 *
 * @param containerWidth  画面の幅(px)
 * @param containerHeight 画面の高さ(px)
 * @param getPlayerScreenPos プレイヤーの画面上タイル座標を取得するコールバック
 */
export default function IsometricCamera({
  className,
  containerWidth = 1200,
  containerHeight = 600,
  getPlayerScreenPos,
  children,
}: IsometricCameraProps) {
  const worldRef = useRef<HTMLDivElement | null>(null);

  useRafLoop(() => {
    const { x, y, layer } = getPlayerScreenPos();
    const pos = getTilePosition(x, y, layer);

    // プレイヤーの画面座標を取得して、カメラを移動
    if (worldRef.current) {
      // // posの中にpxX, pxYがあるのでtransformで移動
      // const nextTransform = `translate(${-pos.pxX + containerWidth / 2}px, ${-pos.pxY + containerHeight / 2}px)`; // 画面中央にプレイヤーを配置
      // worldRef.current.style.transform = nextTransform;
      // console.info(`IsometricCamera: (${x}, ${y}, ${layer}) -> (${pos.pxX}, ${pos.pxY})`);
    }
  });

  // transformの初期値はcontainerの中心に合わせる
  // (プレイヤーが画面中央に来るように)
  // const initialTransform = `translate(${containerWidth / 2}px, ${containerHeight / 2}px)`;

  return (
    <div id="world" ref={worldRef} className={className}>
      {children}
    </div>
  );
}
