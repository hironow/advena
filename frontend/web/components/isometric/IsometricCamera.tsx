'use client';

import React, { useRef } from 'react';
import { useRafLoop } from '../../hooks/use-ref-loop';

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
    if (!worldRef.current) return;

    const { x, y, layer } = getPlayerScreenPos();

    // プレイヤーの画面座標を取得して、カメラを移動
    // 移動は left と top に pxX, pxY を設定することで行う
    // (transform だと中心がずれるため)
    // worldRef.current.style.left = `${containerWidth / 2 + pxX}px`;
    // worldRef.current.style.top = `${containerHeight / 2 + pxY}px`;
  });

  // transformの初期値はcontainerの中心に合わせる
  // (プレイヤーが画面中央に来るように)
  // const initialTransform = `translate(${containerWidth / 2}px, ${containerHeight / 2}px)`;

  return (
    <div
      // "world" 要素。ワールド(背景+プレイヤー等)全体をこの中に入れる
      ref={worldRef}
      className={className}
    >
      {children}
    </div>
  );
}
