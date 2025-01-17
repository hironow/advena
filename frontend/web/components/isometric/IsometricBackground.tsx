'use client';

import React from 'react';
import {
  WORLD_SIZE,
  dummy_tile_map,
  dummy_layer_map,
  zero_layer_map,
} from './tileset';
import Tile from './Tile';

export default function IsometricBackground() {
  // タイル要素をまとめて生成
  const tiles = [];
  for (let y = 0; y < WORLD_SIZE; y++) {
    for (let x = 0; x < WORLD_SIZE; x++) {
      tiles.push(
        <Tile
          key={`tile-${x}-${y}`}
          tile={dummy_tile_map[x][y]}
          x={x}
          y={y}
          layer={dummy_layer_map[x][y]}
        />,
      );
    }
  }

  return <div>{tiles}</div>;
}
