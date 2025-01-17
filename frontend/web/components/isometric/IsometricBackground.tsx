'use client';

import React from 'react';
import { WORLD_SIZE } from './tileset';
import Tile from './Tile';

interface IsometricBackgroundProps {
  map: string[][];
  layerMap: number[][];
  className?: string;
}

export default function IsometricBackground({
  map,
  layerMap,
  className,
}: IsometricBackgroundProps) {
  // タイル要素をまとめて生成
  const tiles = [];
  for (let y = 0; y < WORLD_SIZE; y++) {
    for (let x = 0; x < WORLD_SIZE; x++) {
      tiles.push(
        <Tile
          key={`tile-${x}-${y}`}
          tile={map[x][y]}
          x={x}
          y={y}
          layer={layerMap[x][y]}
        />,
      );
    }
  }

  return <div className={className}>{tiles}</div>;
}
