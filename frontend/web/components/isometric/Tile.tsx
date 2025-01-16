'use client';

import React from 'react';
import Image from 'next/image';
import {
  getTilePosition,
  TILE_IMG_HEIGHT,
  TILE_IMG_WIDTH,
  TILE_SCALE,
  dummy_layer_map,
  type TileSetName,
} from './tileset';

// bird1が見えないので、clock1に変更

interface TileProps {
  tile: TileSetName;
  x: number;
  y: number;
  layer: number;
  reverse?: boolean;
}

const Tile: React.FC<TileProps> = ({ tile, x, y, layer, reverse }) => {
  const { pxX, pxY } = getTilePosition(x, y, layer);

  let img_style = {};
  if (reverse) {
    img_style = {
      transform: 'scaleX(-1)',
    };
  }

  return (
    <div
      key={`tile-${x}-${y}`}
      style={{
        position: 'absolute',
        // 原点(0, 0)は左上なので、左上を中心に配置するためにオフセット
        left: pxX, // 右にx座標
        top: pxY, // 下にy座標
        width: TILE_IMG_WIDTH * TILE_SCALE,
        height: TILE_IMG_HEIGHT * TILE_SCALE,
        // Imageの中心を原点(0, 0)へ (tile画像の下揃え中央が基準点になる)
        transform: 'translate(-50%, -100%)',
      }}
    >
      <Image
        className="object-contain"
        src={`/assets/city_game_tileset/${tile}`}
        alt={`${tile} tile: (${x}, ${y}) = (${pxX}, ${pxY})`}
        width={TILE_IMG_WIDTH}
        height={TILE_IMG_HEIGHT}
        style={img_style}
      />
    </div>
  );
};

export default Tile;
