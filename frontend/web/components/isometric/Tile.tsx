'use client';

import React from 'react';
import Image from 'next/image';
import {
  getTilePosition,
  TILE_IMG_HEIGHT,
  TILE_IMG_WIDTH,
  TILE_SCALE,
  type TileSetName,
} from './tileset';

// bird1が見えないので、clock1に変更

interface TileProps {
  tile: TileSetName;
  x: number;
  y: number;
  layer: number;
  flip?: boolean;
}

const Tile: React.FC<TileProps> = ({ tile, x, y, layer, flip }) => {
  const { pxX, pxY } = getTilePosition(x, y, layer);

  let img_style = {
    WebkitTouchCallout: 'none',
    WebkitUserDrag: 'none',
    userDrag: 'none',
    WebkitUserSelect: 'none',
    userSelect: 'none',
  };
  if (flip) {
    img_style = {
      ...img_style,
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
        // 長押し、強押しでの画像保存を禁止
        WebkitTouchCallout: 'none',
        // dragも禁止
        WebkitUserDrag: 'none',
        userDrag: 'none',
        // 選択時のハイライトを禁止
        WebkitUserSelect: 'none',
        userSelect: 'none',
      }}
    >
      <Image
        className="tile object-contain"
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
