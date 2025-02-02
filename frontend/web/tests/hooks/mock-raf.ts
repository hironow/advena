let nextHandle = 1;
const handleMap = new Map<number, ReturnType<typeof setTimeout>>();

export function mockRequestAnimationFrame(cb: FrameRequestCallback): number {
  const handle = nextHandle++;
  const timerId = setTimeout(() => {
    cb(performance.now());
    handleMap.delete(handle);
  }, 16);

  handleMap.set(handle, timerId);
  return handle; // 独自のIDを返す
}

export function mockCancelAnimationFrame(handle: number) {
  const timerId = handleMap.get(handle);
  if (timerId) {
    clearTimeout(timerId);
    handleMap.delete(handle);
  }
}
