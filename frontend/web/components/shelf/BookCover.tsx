import React, { memo } from 'react';
import { Book } from './book';
import Image from 'next/image';

interface BookCoverProps {
  book: Book;
  index: number;
  centerIndex: number;
  totalBooks: number;
  onSelect: (index: number) => void; // クリック時のコールバック追加
}

function BookCoverComponent({
  book,
  index,
  centerIndex,
  totalBooks,
  onSelect,
}: BookCoverProps) {
  const distance = Math.abs(index - centerIndex);
  const maxDistance = Math.floor(totalBooks / 2);

  // --- 回転などを少しマイルドに変更 ---
  const rotationY = (distance / maxDistance) * 90; // 最大40度回転
  const rotationX = (distance / maxDistance) * 0; // 少し傾ける5
  const translateZ = -distance * 100; // 奥行きを控えめに30
  const scale = 1 - (distance / maxDistance) * 0.9; // 中心から離れるほど小さく0.3
  const zIndex = totalBooks - distance;

  // インデックスが左なら正方向、右なら負方向に回転
  const rotateYAngle = index < centerIndex ? rotationY : -rotationY;

  return (
    <div
      className="relative cursor-pointer will-change-transform"
      style={{
        // 中心からの x 座標移動 (1冊あたり 120px 間隔前提)
        transform: `
          translateX(${(index - centerIndex) * 120}px)
          translateZ(${translateZ}px)
          rotateY(${rotateYAngle}deg)
          rotateX(${rotationX}deg)
          scale(${scale})
        `,
        zIndex,
        transition: 'transform 0.3s ease-out',
        // backfaceVisibility: 'hidden',
      }}
      onClick={() => onSelect(index)} // クリックしたら中央へ
    >
      <Image
        src={book.coverUrl}
        alt={book.title}
        className="object-contain transform-gpu"
        width={32 * 4}
        height={48 * 4}
      />
      <div className="absolute bottom-0 left-0 right-0 bg-gray-800 bg-opacity-50 text-white p-2 text-center">
        <p className="text-sm font-bold truncate">{book.title}</p>
        <p className="text-xs truncate">{book.author}</p>
      </div>
    </div>
  );
}

// 余計な再レンダリングを防ぐために React.memo でラップ
export const BookCover = memo(BookCoverComponent);
