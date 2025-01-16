// タイル画像の実サイズ (px)。今回は 382x805 でタイルは全て下揃えで揃っている前提
export const TILE_IMG_WIDTH = 382;
export const TILE_IMG_HEIGHT = 805;

// 縮小率。実際の画面サイズに合わせて調整
export const TILE_SCALE = 0.4;

// ワールド(マップ)のサイズで「マス」今回は 10x10 の正方形のマップ
export const WORLD_SIZE = 10;

// 初期リスポーン地点: 真下の1つ上のマス
export const START_X = WORLD_SIZE - 2;
export const START_Y = WORLD_SIZE - 2;

/**
 * isometricなpx座標を算出する (マス座標 -> px座標)
 * xIndex, yIndex: タイルのマス座標 (0 <= x, y < WORLD_SIZE) (0, 0) が頂上で、右下に行くほどx増加、左下に行くほどy増加
 * layer: タイルのレイヤー (0 <= layer < 10) 0がベースで9が最上層の全10層のレイヤー (半タイルは1層上げるとピッタリ、全タイルは2層上げるとピッタリ)
 */
export function getTilePosition(xIndex: number, yIndex: number, layer: number) {
  // 微調整: 斜めにはおよそ86pxのタイルでpx座標では xに78px、yに38pxずつずれるのがちょうどいい
  const unitX = 78;
  const unitY = 38;

  const diffX = unitX * TILE_SCALE;
  const diffY = unitY * TILE_SCALE;

  const initialX = 0;
  const initialY = 0;

  // layerが上がる = pxYにマイナスがかかる
  let layerDiffY = 0;
  if (layer > 0 && layer < 10) {
    layerDiffY = unitY * TILE_SCALE * layer;
  }

  // xIndex は右下方向
  // yIndex は左下方向
  const pxX = initialX + xIndex * diffX - yIndex * diffX;
  const pxY = initialY + xIndex * diffY + yIndex * diffY - layerDiffY;

  return { pxX, pxY };
}

// ダミー10x10レイヤー情報 描画範囲確認用
export const dummy_layer_map = [
  [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
  [8, 7, 6, 5, 4, 3, 2, 1, 0, 0],
  [7, 6, 5, 4, 3, 2, 1, 0, 0, 0],
  [6, 5, 4, 3, 2, 1, 0, 0, 0, 0],
  [5, 4, 3, 2, 1, 0, 0, 0, 0, 0],
  [4, 3, 2, 1, 0, 0, 0, 0, 0, 0],
  [3, 2, 1, 0, 0, 0, 0, 0, 0, 0],
  [2, 1, 0, 0, 0, 0, 0, 0, 0, 0],
  [1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
];

// tileset filename
export type TileSetName = string;
export const agave1: TileSetName = 'agave1.png';
export const anthill1: TileSetName = 'anthill1.png';
export const arch1: TileSetName = 'arch1.png';
export const bag1: TileSetName = 'bag1.png';
export const balloon1: TileSetName = 'balloon1.png';
export const bamboo1: TileSetName = 'bamboo1.png';
export const barrier1: TileSetName = 'barrier1.png';
export const barrier2: TileSetName = 'barrier2.png';
export const bat1: TileSetName = 'bat1.png';
export const bathtub1: TileSetName = 'bathtub1.png';
export const bear1: TileSetName = 'bear1.png';
export const bed1: TileSetName = 'bed1.png';
export const bee1: TileSetName = 'bee1.png';
export const beetle1: TileSetName = 'beetle1.png';
export const bench1: TileSetName = 'bench1.png';
export const bicycle1: TileSetName = 'bicycle1.png';
export const bike_rack1: TileSetName = 'bike-rack1.png';
export const bird1: TileSetName = 'bird1.png';
export const bird2: TileSetName = 'bird2.png';
export const bird3: TileSetName = 'bird3.png';
export const bird4: TileSetName = 'bird4.png';
export const bird5: TileSetName = 'bird5.png';
export const bird6: TileSetName = 'bird6.png';
export const bone1: TileSetName = 'bone1.png';
export const book1: TileSetName = 'book1.png';
export const book2: TileSetName = 'book2.png';
export const book3: TileSetName = 'book3.png';
export const bookshelf1: TileSetName = 'bookshelf1.png';
export const bowl1: TileSetName = 'bowl1.png';
export const box1: TileSetName = 'box1.png';
export const branch1: TileSetName = 'branch1.png';
export const branch2: TileSetName = 'branch2.png';
export const brick1: TileSetName = 'brick1.png';
export const broom1: TileSetName = 'broom1.png';
export const bubble1: TileSetName = 'bubble1.png';
export const bush1: TileSetName = 'bush1.png';
export const bush2: TileSetName = 'bush2.png';
export const bush3: TileSetName = 'bush3.png';
export const bush4: TileSetName = 'bush4.png';
export const butterfly1: TileSetName = 'butterfly1.png';
export const butterfly2: TileSetName = 'butterfly2.png';
export const cabbage1: TileSetName = 'cabbage1.png';
export const cactus1: TileSetName = 'cactus1.png';
export const calculator1: TileSetName = 'calculator1.png';
export const campfire1: TileSetName = 'campfire1.png';
export const canoe1: TileSetName = 'canoe1.png';
export const card1: TileSetName = 'card1.png';
export const carrot1: TileSetName = 'carrot1.png';
export const castle1: TileSetName = 'castle1.png';
export const cat1: TileSetName = 'cat1.png';
export const cat2: TileSetName = 'cat2.png';
export const caution_sign1: TileSetName = 'caution-sign1.png';
export const cellar1: TileSetName = 'cellar1.png';
export const cement_pipe1: TileSetName = 'cement-pipe1.png';
export const chair1: TileSetName = 'chair1.png';
export const chair2: TileSetName = 'chair2.png';
export const chair3: TileSetName = 'chair3.png';
export const chest1: TileSetName = 'chest1.png';
export const cinderblock1: TileSetName = 'cinderblock1.png';
export const clock1: TileSetName = 'clock1.png';
export const cloud1: TileSetName = 'cloud1.png';
export const cloud2: TileSetName = 'cloud2.png';
export const cloud3: TileSetName = 'cloud3.png';
export const cloud4: TileSetName = 'cloud4.png';
export const coin1: TileSetName = 'coin1.png';
export const column1: TileSetName = 'column1.png';
export const cone1: TileSetName = 'cone1.png';
export const cone2: TileSetName = 'cone2.png';
export const cookiejar1: TileSetName = 'cookiejar1.png';
export const couch1: TileSetName = 'couch1.png';
export const cow1: TileSetName = 'cow1.png';
export const cow2: TileSetName = 'cow2.png';
export const coyote1: TileSetName = 'coyote1.png';
export const crab1: TileSetName = 'crab1.png';
export const crow1: TileSetName = 'crow1.png';
export const crown1: TileSetName = 'crown1.png';
export const curtains1: TileSetName = 'curtains1.png';
export const cushion1: TileSetName = 'cushion1.png';
export const dandelion1: TileSetName = 'dandelion1.png';
export const deer1: TileSetName = 'deer1.png';
export const desk1: TileSetName = 'desk1.png';
export const dice1: TileSetName = 'dice1.png';
export const dirt1: TileSetName = 'dirt1.png';
export const dog1: TileSetName = 'dog1.png';
export const doll1: TileSetName = 'doll1.png';
export const donkey1: TileSetName = 'donkey1.png';
export const door1: TileSetName = 'door1.png';
export const dress1: TileSetName = 'dress1.png';
export const dresser1: TileSetName = 'dresser1.png';
export const drink1: TileSetName = 'drink1.png';
export const drum1: TileSetName = 'drum1.png';
export const duck1: TileSetName = 'duck1.png';
export const duck2: TileSetName = 'duck2.png';
export const dumpster1: TileSetName = 'dumpster1.png';
export const dust1: TileSetName = 'dust1.png';
export const dust2: TileSetName = 'dust2.png';
export const ear1: TileSetName = 'ear1.png';
export const egg1: TileSetName = 'egg1.png';
export const egg2: TileSetName = 'egg2.png';
export const eggplant1: TileSetName = 'eggplant1.png';
export const elevator1: TileSetName = 'elevator1.png';
export const envelope1: TileSetName = 'envelope1.png';
export const eye1: TileSetName = 'eye1.png';
export const feather1: TileSetName = 'feather1.png';
export const fire_extinguisher1: TileSetName = 'fire-extinguisher1.png';
export const fire_hydrant1: TileSetName = 'fire-hydrant1.png';
export const fire1: TileSetName = 'fire1.png';
export const flower1: TileSetName = 'flower1.png';
export const flower2: TileSetName = 'flower2.png';
export const flower3: TileSetName = 'flower3.png';
export const flower4: TileSetName = 'flower4.png';
export const fox1: TileSetName = 'fox1.png';
export const frog1: TileSetName = 'frog1.png';
export const fruit_tree1: TileSetName = 'fruit-tree1.png';
export const fungus1: TileSetName = 'fungus1.png';
export const gas_can1: TileSetName = 'gas-can1.png';
export const gate1: TileSetName = 'gate1.png';
export const ghost1: TileSetName = 'ghost1.png';
export const globe1: TileSetName = 'globe1.png';
export const goat1: TileSetName = 'goat1.png';
export const goose1: TileSetName = 'goose1.png';
export const grass1: TileSetName = 'grass1.png';
export const grass2: TileSetName = 'grass2.png';
export const grass3: TileSetName = 'grass3.png';
export const grass4: TileSetName = 'grass4.png';
export const grass5: TileSetName = 'grass5.png';
export const grass6: TileSetName = 'grass6.png';
export const grass7: TileSetName = 'grass7.png';
export const grave1: TileSetName = 'grave1.png';
export const grave2: TileSetName = 'grave2.png';
export const greenhouse1: TileSetName = 'greenhouse1.png';
export const ground_tile_foliage1: TileSetName = 'ground_tile_foliage1.png';
export const ground_tile_foliage2: TileSetName = 'ground_tile_foliage2.png';
export const ground_tile_porous1: TileSetName = 'ground_tile_porous1.png';
export const ground_tile_porous2: TileSetName = 'ground_tile_porous2.png';
export const hammer1: TileSetName = 'hammer1.png';
export const hedgehog1: TileSetName = 'hedgehog1.png';
export const hoop1: TileSetName = 'hoop1.png';
export const horse1: TileSetName = 'horse1.png';
export const hose1: TileSetName = 'hose1.png';
export const house1: TileSetName = 'house1.png';
export const house2: TileSetName = 'house2.png';
export const house3: TileSetName = 'house3.png';
export const houseplant1: TileSetName = 'houseplant1.png';
export const houseplant2: TileSetName = 'houseplant2.png';
export const houseplant3: TileSetName = 'houseplant3.png';
export const houseplant4: TileSetName = 'houseplant4.png';
export const ladder1: TileSetName = 'ladder1.png';
export const lamp1: TileSetName = 'lamp1.png';
export const lamp2: TileSetName = 'lamp2.png';
export const laptop1: TileSetName = 'laptop1.png';
export const laundry1: TileSetName = 'laundry1.png';
export const leaf1: TileSetName = 'leaf1.png';
export const leaf2: TileSetName = 'leaf2.png';
export const leaf3: TileSetName = 'leaf3.png';
export const lion1: TileSetName = 'lion1.png';
export const logs1: TileSetName = 'logs1.png';
export const manhole1: TileSetName = 'manhole1.png';
export const memorial1: TileSetName = 'memorial1.png';
export const milemarker1: TileSetName = 'milemarker1.png';
export const monument1: TileSetName = 'monument1.png';
export const monument2: TileSetName = 'monument2.png';
export const monument3: TileSetName = 'monument3.png';
export const mop1: TileSetName = 'mop1.png';
export const moss1: TileSetName = 'moss1.png';
export const moss2: TileSetName = 'moss2.png';
export const mug1: TileSetName = 'mug1.png';
export const nest1: TileSetName = 'nest1.png';
export const outdoor_light1: TileSetName = 'outdoor-light1.png';
export const palm1: TileSetName = 'palm1.png';
export const palm2: TileSetName = 'palm2.png';
export const paper1: TileSetName = 'paper1.png';
export const path1: TileSetName = 'path1.png';
export const pea1: TileSetName = 'pea1.png';
export const pebble1: TileSetName = 'pebble1.png';
export const pebble2: TileSetName = 'pebble2.png';
export const pencil1: TileSetName = 'pencil1.png';
export const pencil2: TileSetName = 'pencil2.png';
export const person1: TileSetName = 'person1.png';
export const person2: TileSetName = 'person2.png';
export const person3: TileSetName = 'person3.png';
export const person4: TileSetName = 'person4.png';
export const person5: TileSetName = 'person5.png';
export const person6: TileSetName = 'person6.png';
export const pier1: TileSetName = 'pier1.png';
export const pine1: TileSetName = 'pine1.png';
export const pine2: TileSetName = 'pine2.png';
export const plank1: TileSetName = 'plank1.png';
export const plank2: TileSetName = 'plank2.png';
export const plank3: TileSetName = 'plank3.png';
export const pole1: TileSetName = 'pole1.png';
export const possum1: TileSetName = 'possum1.png';
export const power1: TileSetName = 'power1.png';
export const present1: TileSetName = 'present1.png';
export const puddle1: TileSetName = 'puddle1.png';
export const puddle2: TileSetName = 'puddle2.png';
export const puddle3: TileSetName = 'puddle3.png';
export const pump1: TileSetName = 'pump1.png';
export const pumpkin1: TileSetName = 'pumpkin1.png';
export const pyramid1: TileSetName = 'pyramid1.png';
export const pyramid2: TileSetName = 'pyramid2.png';
export const pyramid3: TileSetName = 'pyramid3.png';
export const rabbit1: TileSetName = 'rabbit1.png';
export const rabbit2: TileSetName = 'rabbit2.png';
export const radish1: TileSetName = 'radish1.png';
export const rail1: TileSetName = 'rail1.png';
export const reed2: TileSetName = 'reed2.png';
export const reeds1: TileSetName = 'reeds1.png';
export const road1: TileSetName = 'road1.png';
export const rock1: TileSetName = 'rock1.png';
export const rock2: TileSetName = 'rock2.png';
export const rock3: TileSetName = 'rock3.png';
export const rose1: TileSetName = 'rose1.png';
export const rubble1: TileSetName = 'rubble1.png';
export const rubble2: TileSetName = 'rubble2.png';
export const sand1: TileSetName = 'sand1.png';
export const sand2: TileSetName = 'sand2.png';
export const sand3: TileSetName = 'sand3.png';
export const sand4: TileSetName = 'sand4.png';
export const sandal1: TileSetName = 'sandal1.png';
export const satellite_dish1: TileSetName = 'satellite-dish1.png';
export const satellite1: TileSetName = 'satellite1.png';
export const satellite2: TileSetName = 'satellite2.png';
export const seed1: TileSetName = 'seed1.png';
export const ship1: TileSetName = 'ship1.png';
export const shoe1: TileSetName = 'shoe1.png';
export const silo1: TileSetName = 'silo1.png';
export const slate1: TileSetName = 'slate1.png';
export const sprouts1: TileSetName = 'sprouts1.png';
export const squash1: TileSetName = 'squash1.png';
export const squash2: TileSetName = 'squash2.png';
export const stair1: TileSetName = 'stair1.png';
export const stair2: TileSetName = 'stair2.png';
export const stair3: TileSetName = 'stair3.png';
export const stair4: TileSetName = 'stair4.png';
export const stool1: TileSetName = 'stool1.png';
export const stop_sign1: TileSetName = 'stop-sign1.png';
export const streetlight1: TileSetName = 'streetlight1.png';
export const streetlight2: TileSetName = 'streetlight2.png';
export const stump1: TileSetName = 'stump1.png';
export const sun1: TileSetName = 'sun1.png';
export const sun2: TileSetName = 'sun2.png';
export const sun3: TileSetName = 'sun3.png';
export const teddybear1: TileSetName = 'teddybear1.png';
export const telephone_booth1: TileSetName = 'telephone-booth1.png';
export const telescope1: TileSetName = 'telescope1.png';
export const tent1: TileSetName = 'tent1.png';
export const tent2: TileSetName = 'tent2.png';
export const tiger1: TileSetName = 'tiger1.png';
export const tile1: TileSetName = 'tile1.png';
export const tile2: TileSetName = 'tile2.png';
export const tile3: TileSetName = 'tile3.png';
export const tire1: TileSetName = 'tire1.png';
export const toilet1: TileSetName = 'toilet1.png';
export const tomato1: TileSetName = 'tomato1.png';
export const tomb1: TileSetName = 'tomb1.png';
export const tower1: TileSetName = 'tower1.png';
export const track1: TileSetName = 'track1.png';
export const traffic_circle1: TileSetName = 'traffic-circle1.png';
export const traffic_sign1: TileSetName = 'traffic-sign1.png';
export const trash1: TileSetName = 'trash1.png';
export const trashcan1: TileSetName = 'trashcan1.png';
export const tree1: TileSetName = 'tree1.png';
export const tree2: TileSetName = 'tree2.png';
export const tree3: TileSetName = 'tree3.png';
export const tree4: TileSetName = 'tree4.png';
export const tree5: TileSetName = 'tree5.png';
export const tropical1: TileSetName = 'tropical1.png';
export const tropical2: TileSetName = 'tropical2.png';
export const tropical3: TileSetName = 'tropical3.png';
export const turret1: TileSetName = 'turret1.png';
export const twig1: TileSetName = 'twig1.png';
export const twig2: TileSetName = 'twig2.png';
export const umbrella1: TileSetName = 'umbrella1.png';
export const vine1: TileSetName = 'vine1.png';
export const water1: TileSetName = 'water1.png';
export const weasel1: TileSetName = 'weasel1.png';
export const well1: TileSetName = 'well1.png';
export const window1: TileSetName = 'window1.png';
export const wolf1: TileSetName = 'wolf1.png';
export const wood1: TileSetName = 'wood1.png';
