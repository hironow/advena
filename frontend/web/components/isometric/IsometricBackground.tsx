'use client';

import React from 'react';
import Image from 'next/image';
import {
  dummy_layer_map,
  getTilePosition,
  TILE_IMG_HEIGHT,
  TILE_IMG_WIDTH,
  TILE_SCALE,
  WORLD_SIZE,
} from './tileset';

interface IsometricBackgroundProps {
  className?: string;
}

const IsometricBackground: React.FC<IsometricBackgroundProps> = ({
  className,
}) => {
  // タイル要素をまとめて生成
  const tiles = [];
  for (let y = 0; y < WORLD_SIZE; y++) {
    for (let x = 0; x < WORLD_SIZE; x++) {
      // 座標変換 (マス座標 -> px座標)
      // レイヤーも加味する
      const layer = dummy_layer_map[x][y];
      const { pxX, pxY } = getTilePosition(x, y, layer);

      tiles.push(
        <div
          key={`tile-${x}-${y}`}
          style={{
            position: 'absolute',
            // 原点(0, 0)は左上なので、左上を中心に配置するためにオフセット
            left: pxX, // 右にx座標
            top: pxY, // 下にy座標
            width: TILE_IMG_WIDTH * TILE_SCALE,
            height: TILE_IMG_HEIGHT * TILE_SCALE,
            // 中心を原点(0, 0)から、下揃え中央にするためにオフセット
            transform: 'translate(50%, 100%)',
          }}
        >
          <Image
            src="/assets/city_game_tileset/brick1.png"
            alt={`tile: (${x}, ${y}) = (${pxX}, ${pxY})`}
            width={TILE_IMG_WIDTH}
            height={TILE_IMG_HEIGHT}
          />
        </div>,
      );
    }

    // break;
  }

  return (
    <div
      className={className}
      style={{
        position: 'relative',
      }}
    >
      {tiles}
    </div>
  );
};

export default IsometricBackground;
