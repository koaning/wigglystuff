export function pointKey(point) {
  return `${point[0]},${point[1]}`;
}

export function canonicalSegment(a, b) {
  const first = a[0] < b[0] || (a[0] === b[0] && a[1] <= b[1]) ? a : b;
  const second = first === a ? b : a;
  return [first, second];
}

export function segmentKey(a, b) {
  const [first, second] = canonicalSegment(a, b);
  return `${pointKey(first)}|${pointKey(second)}`;
}

export function segmentUnderPosition(pos, layout) {
  const localX = pos.x - layout.padding;
  const localY = pos.y - layout.padding;
  const tolerance = Math.max(10, Math.min(layout.cellWidth, layout.cellHeight) * 0.35);
  const candidates = [];

  const hRow = Math.round(localY / layout.cellHeight);
  const hCol = Math.floor(localX / layout.cellWidth);
  if (hRow >= 0 && hRow <= layout.rows && hCol >= 0 && hCol < layout.cols) {
    const y = hRow * layout.cellHeight;
    const x1 = hCol * layout.cellWidth;
    const x2 = (hCol + 1) * layout.cellWidth;
    if (localX >= x1 - tolerance && localX <= x2 + tolerance) {
      candidates.push({
        distance: Math.abs(localY - y),
        from: [hRow, hCol],
        to: [hRow, hCol + 1],
      });
    }
  }

  const vCol = Math.round(localX / layout.cellWidth);
  const vRow = Math.floor(localY / layout.cellHeight);
  if (vCol >= 0 && vCol <= layout.cols && vRow >= 0 && vRow < layout.rows) {
    const x = vCol * layout.cellWidth;
    const y1 = vRow * layout.cellHeight;
    const y2 = (vRow + 1) * layout.cellHeight;
    if (localY >= y1 - tolerance && localY <= y2 + tolerance) {
      candidates.push({
        distance: Math.abs(localX - x),
        from: [vRow, vCol],
        to: [vRow + 1, vCol],
      });
    }
  }

  candidates.sort((a, b) => a.distance - b.distance);
  return candidates.length > 0 && candidates[0].distance <= tolerance ? candidates[0] : null;
}

export function traceSegmentsBetweenPositions(start, end, layout) {
  const distance = Math.hypot(end.x - start.x, end.y - start.y);
  const step = Math.max(2, Math.min(layout.cellWidth, layout.cellHeight) / 4);
  const sampleCount = Math.max(1, Math.ceil(distance / step));
  const segments = [];
  const seen = new Set();

  for (let i = 0; i <= sampleCount; i += 1) {
    const t = i / sampleCount;
    const pos = {
      x: start.x + (end.x - start.x) * t,
      y: start.y + (end.y - start.y) * t,
    };
    const segment = segmentUnderPosition(pos, layout);
    if (!segment) {
      continue;
    }
    const key = segmentKey(segment.from, segment.to);
    if (!seen.has(key)) {
      seen.add(key);
      segments.push(segment);
    }
  }

  return segments;
}
