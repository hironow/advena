'use client';

import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { useAudioContextState } from './audio-context-provider';

const LedVisualizer: React.FC<{ width?: number; height?: number }> = ({
  width = 600,
  height = 300,
}) => {
  const { freqData } = useAudioContextState();
  const svgRef = useRef<SVGSVGElement>(null);
  const initedRef = useRef(false);

  const binCount = freqData?.length || 256;
  const xScale = d3
    .scaleLinear()
    .domain([0, binCount - 1])
    .range([0, width]);
  const yScale = d3.scaleLinear().domain([0, 255]).range([height, 0]);
  const colorScale = d3
    .scaleSequential(d3.interpolateSpectral) // スペクトル なので interpolateSpectral で。他には interpolateViridis, interpolateInferno, interpolateRdYlBu, interpolatePlasma が良さそう
    .domain([0, binCount - 1]);

  // 初期化
  useEffect(() => {
    if (!svgRef.current) return;
    d3.select(svgRef.current).selectAll('*').remove();

    d3.select(svgRef.current)
      .append('g')
      .attr('class', 'led-border')
      .attr('stroke-width', 0.0)
      .attr('stroke', 'white')
      .call(
        d3
          .axisLeft(yScale)
          .ticks(8)
          .tickSize(-width)
          .tickFormat(() => ''),
      );
    initedRef.current = true;
  }, [width, height]);

  // freqData更新時
  useEffect(() => {
    if (!initedRef.current || !svgRef.current || !freqData) return;

    const svg = d3.select(svgRef.current);
    const selection = svg
      .selectAll<SVGRectElement, number>('rect')
      .data(freqData);

    // ENTER
    selection
      .enter()
      .append('rect')
      .attr('x', (_, i) => xScale(i))
      .attr('width', xScale(1) - xScale(0))
      .attr('fill', (_, i) => colorScale(i))
      .attr('y', yScale(0))
      .attr('height', 0)
      .attr('opacity', 0.7);

    // UPDATE
    selection
      .transition()
      .duration(50)
      .attr('fill', (_, i) => colorScale(i))
      .attr('y', (d) => yScale(d))
      .attr('height', (d) => yScale(0) - yScale(d));

    // EXIT
    selection.exit().remove();
  }, [freqData]);

  return (
    <svg
      ref={svgRef}
      width={width}
      height={height}
      style={{ background: '#222' }}
    />
  );
};

export default LedVisualizer;
