import assert from "node:assert/strict";

import {
  segmentKey,
  traceSegmentsBetweenPositions,
} from "../js/grid-draw/geometry.mjs";

const layout = {
  rows: 4,
  cols: 4,
  padding: 10,
  cellWidth: 20,
  cellHeight: 20,
};

function keys(segments) {
  return segments.map((segment) => segmentKey(segment.from, segment.to));
}

const horizontalSegments = traceSegmentsBetweenPositions(
  { x: 39, y: 30 },
  { x: 79, y: 30 },
  layout,
);

assert.deepEqual(keys(horizontalSegments), [
  "1,1|1,2",
  "1,2|1,3",
  "1,3|1,4",
]);

const verticalSegments = traceSegmentsBetweenPositions(
  { x: 50, y: 39 },
  { x: 50, y: 79 },
  layout,
);

assert.deepEqual(keys(verticalSegments), [
  "1,2|2,2",
  "2,2|3,2",
  "3,2|4,2",
]);
