(function() {
  var D3LinePlotter;

  D3LinePlotter = class D3LinePlotter {
    constructor(container, options = {}) {
      this.container = container;
      this.options = options;
      this.width = this.options.width || 800;
      this.height = this.options.height || 400;
      this.margin = this.options.margin || {
        top: 20,
        right: 70,
        bottom: 80,
        left: 50
      };
      this.innerWidth = this.width - this.margin.left - this.margin.right;
      this.innerHeight = this.height - this.margin.top - this.margin.bottom;
      
      // Initialize SVG
      this.svg = d3.select(this.container).append('svg').attr('width', this.width).attr('height', this.height);
      this.g = this.svg.append('g').attr('transform', `translate(${this.margin.left},${this.margin.top})`);
      
      // Initialize scales
      this.xScale = d3.scaleTime().range([0, this.innerWidth]);
      this.yScale = d3.scaleLinear().range([
        this.innerHeight,
        0 // Left Y-axis
      ]);
      this.yScaleRight = d3.scaleLinear().range([
        this.innerHeight,
        0 // Right Y-axis
      ]);
      
      // Initialize line generators
      this.line = d3.line().x((d) => {
        return this.xScale(d.x);
      }).y((d) => {
        return this.yScale(d.y);
      }).curve(d3.curveMonotoneX);
      this.lineRight = d3.line().x((d) => {
        return this.xScale(d.x);
      }).y((d) => {
        return this.yScaleRight(d.y);
      }).curve(d3.curveMonotoneX);
    }

    parseData(rawData) {
      var hlineData, j, k, len, len1, lineData, parsedData, point, ref, series, useRightAxis;
      parsedData = {
        linesLeft: [],
        linesRight: [],
        hlinesLeft: [],
        hlinesRight: [],
        leftAxisTitle: 'Left Axis',
        rightAxisTitle: 'Right Axis'
      };
      for (j = 0, len = rawData.length; j < len; j++) {
        series = rawData[j];
        // Determine which Y-axis to use (default to left)
        useRightAxis = series.y_axis === 'right';
        
        // Set axis titles if provided
        if (series.left_axis_title) {
          parsedData.leftAxisTitle = series.left_axis_title;
        }
        if (series.right_axis_title) {
          parsedData.rightAxisTitle = series.right_axis_title;
        }
        if (series.plot_type === 'line') {
          lineData = {
            color: series.plot_color,
            showPoints: series.show_points,
            lineStyle: series.line_style || 'solid', // solid, dashed, dotted
            points: []
          };
          ref = series.plot_points;
          for (k = 0, len1 = ref.length; k < len1; k++) {
            point = ref[k];
            lineData.points.push({
              x: new Date(point.x.value),
              y: parseFloat(point.y.value)
            });
          }
          if (useRightAxis) {
            parsedData.linesRight.push(lineData);
          } else {
            parsedData.linesLeft.push(lineData);
          }
        } else if (series.plot_type === 'hline') {
          hlineData = {
            color: series.plot_color,
            y: parseFloat(series.plot_points[0].y.value),
            lineStyle: series.line_style || 'dashed'
          };
          if (useRightAxis) {
            parsedData.hlinesRight.push(hlineData);
          } else {
            parsedData.hlinesLeft.push(hlineData);
          }
        }
      }
      return parsedData;
    }

    getLineStylePattern(style) {
      switch (style) {
        case 'solid':
          return 'none';
        case 'dashed':
          return '10,5';
        case 'dotted':
          return '3,3';
        case 'dash-dot':
          return '10,5,3,5';
        default:
          return 'none';
      }
    }

    updateScales(data) {
      var allXValues, hline, j, k, l, leftExtent, leftPadding, leftRange, leftYValues, len, len1, len2, len3, len4, len5, line, m, n, o, point, ref, ref1, ref2, ref3, ref4, ref5, rightExtent, rightPadding, rightRange, rightYValues;
      // Get all x values from line data
      allXValues = [];
      leftYValues = [];
      rightYValues = [];
      ref = data.linesLeft;
      
      // Collect left axis data
      for (j = 0, len = ref.length; j < len; j++) {
        line = ref[j];
        ref1 = line.points;
        for (k = 0, len1 = ref1.length; k < len1; k++) {
          point = ref1[k];
          allXValues.push(point.x);
          leftYValues.push(point.y);
        }
      }
      ref2 = data.hlinesLeft;
      for (l = 0, len2 = ref2.length; l < len2; l++) {
        hline = ref2[l];
        leftYValues.push(hline.y);
      }
      ref3 = data.linesRight;
      
      // Collect right axis data
      for (m = 0, len3 = ref3.length; m < len3; m++) {
        line = ref3[m];
        ref4 = line.points;
        for (n = 0, len4 = ref4.length; n < len4; n++) {
          point = ref4[n];
          allXValues.push(point.x);
          rightYValues.push(point.y);
        }
      }
      ref5 = data.hlinesRight;
      for (o = 0, len5 = ref5.length; o < len5; o++) {
        hline = ref5[o];
        rightYValues.push(hline.y);
      }
      
      // Set X scale domain
      this.xScale.domain(d3.extent(allXValues));
      
      // Set Y scale domains with padding
      if (leftYValues.length > 0) {
        leftExtent = d3.extent(leftYValues);
        leftRange = leftExtent[1] - leftExtent[0];
        leftPadding = leftRange * 0.1;
        this.yScale.domain([leftExtent[0] - leftPadding, leftExtent[1] + leftPadding]);
      }
      if (rightYValues.length > 0) {
        rightExtent = d3.extent(rightYValues);
        rightRange = rightExtent[1] - rightExtent[0];
        rightPadding = rightRange * 0.1;
        return this.yScaleRight.domain([rightExtent[0] - rightPadding, rightExtent[1] + rightPadding]);
      }
    }

    drawAxes(data) {
      var tickCount, tickFormat, timeDiff, timeRange;
      // X Axis with better date/time formatting
      timeRange = this.xScale.domain();
      timeDiff = timeRange[1] - timeRange[0];
      
      // Choose appropriate format based on time span
      if (timeDiff < 24 * 60 * 60 * 1000) { // Less than 24 hours
        tickFormat = d3.timeFormat('%m/%d %H:%M');
        tickCount = Math.min(8, Math.max(3, Math.floor(this.innerWidth / 100)));
      } else if (timeDiff < 7 * 24 * 60 * 60 * 1000) { // Less than 7 days
        tickFormat = d3.timeFormat('%m/%d %H:%M');
        tickCount = Math.min(10, Math.max(4, Math.floor(this.innerWidth / 80)));
      } else {
        tickFormat = d3.timeFormat('%Y-%m-%d');
        tickCount = Math.min(8, Math.max(3, Math.floor(this.innerWidth / 120)));
      }
      this.g.append('g').attr('class', 'x-axis').attr('transform', `translate(0,${this.innerHeight})`).call(d3.axisBottom(this.xScale).tickFormat(tickFormat).ticks(tickCount));
      
      // Rotate x-axis labels for better readability
      this.g.selectAll('.x-axis text').style('text-anchor', 'end').attr('dx', '-.8em').attr('dy', '.15em').attr('transform', 'rotate(-45)');
      
      // Left Y Axis (integers)
      this.g.append('g').attr('class', 'y-axis-left').call(d3.axisLeft(this.yScale).tickFormat(d3.format('.1f')));
      
      // Right Y Axis (floats) - only if we have right-axis data
      if (this.yScaleRight.domain()[0] !== this.yScaleRight.domain()[1]) {
        this.g.append('g').attr('class', 'y-axis-right').attr('transform', `translate(${this.innerWidth},0)`).call(d3.axisRight(this.yScaleRight).tickFormat(d3.format('.1f')));
      }
      
      // Add axis labels
      this.g.append('text').attr('class', 'axis-label-left').attr('transform', 'rotate(-90)').attr('y', 0 - this.margin.left).attr('x', 0 - (this.innerHeight / 2)).attr('dy', '1em').style('text-anchor', 'middle').text(data.leftAxisTitle);
      
      // Right axis label (only if we have right-axis data)
      if (this.yScaleRight.domain()[0] !== this.yScaleRight.domain()[1]) {
        this.g.append('text').attr('class', 'axis-label-right').attr('transform', 'rotate(-90)').attr('y', this.innerWidth + this.margin.right - 10).attr('x', 0 - (this.innerHeight / 2)).attr('dy', '1em').style('text-anchor', 'middle').text(data.rightAxisTitle);
      }
      return this.g.append('text').attr('class', 'axis-label').attr('transform', `translate(${this.innerWidth / 2}, ${this.innerHeight + this.margin.bottom})`).style('text-anchor', 'middle').text('Time');
    }

    drawHorizontalLines(hlinesLeft, hlinesRight) {
      // Left axis horizontal lines
      this.g.selectAll('.hline-left').data(hlinesLeft).enter().append('line').attr('class', 'hline-left').attr('x1', 0).attr('x2', this.innerWidth).attr('y1', (d) => {
        return this.yScale(d.y);
      }).attr('y2', (d) => {
        return this.yScale(d.y);
      }).attr('stroke', function(d) {
        return d.color;
      }).attr('stroke-width', 2).attr('stroke-dasharray', (d) => {
        return this.getLineStylePattern(d.lineStyle);
      }).attr('opacity', 0.7);
      
      // Right axis horizontal lines
      return this.g.selectAll('.hline-right').data(hlinesRight).enter().append('line').attr('class', 'hline-right').attr('x1', 0).attr('x2', this.innerWidth).attr('y1', (d) => {
        return this.yScaleRight(d.y);
      }).attr('y2', (d) => {
        return this.yScaleRight(d.y);
      }).attr('stroke', function(d) {
        return d.color;
      }).attr('stroke-width', 2).attr('stroke-dasharray', (d) => {
        return this.getLineStylePattern(d.lineStyle);
      }).attr('opacity', 0.7);
    }

    drawLines(linesLeft, linesRight) {
      var i, j, k, len, len1, lineData, results;
      // Draw left axis line paths
      this.g.selectAll('.line-path-left').data(linesLeft).enter().append('path').attr('class', 'line-path-left').attr('d', (d) => {
        return this.line(d.points);
      }).attr('fill', 'none').attr('stroke', function(d) {
        return d.color;
      }).attr('stroke-width', 2).attr('stroke-dasharray', (d) => {
        return this.getLineStylePattern(d.lineStyle);
      });
      
      // Draw right axis line paths
      this.g.selectAll('.line-path-right').data(linesRight).enter().append('path').attr('class', 'line-path-right').attr('d', (d) => {
        return this.lineRight(d.points);
      }).attr('fill', 'none').attr('stroke', function(d) {
        return d.color;
      }).attr('stroke-width', 2).attr('stroke-dasharray', (d) => {
        return this.getLineStylePattern(d.lineStyle);
      });

      // Draw points for left axis lines
      for (i = j = 0, len = linesLeft.length; j < len; i = ++j) {
        lineData = linesLeft[i];
        if (lineData.showPoints) {
          this.g.selectAll(`.point-left-${i}`).data(lineData.points).enter().append('circle').attr('class', `point-left-${i}`).attr('cx', (d) => {
            return this.xScale(d.x);
          }).attr('cy', (d) => {
            return this.yScale(d.y);
          }).attr('r', 4).attr('fill', lineData.color).attr('stroke', 'white').attr('stroke-width', 2);
        }
      }

      // Draw points for right axis lines
      results = [];
      for (i = k = 0, len1 = linesRight.length; k < len1; i = ++k) {
        lineData = linesRight[i];
        if (lineData.showPoints) {
          results.push(this.g.selectAll(`.point-right-${i}`).data(lineData.points).enter().append('circle').attr('class', `point-right-${i}`).attr('cx', (d) => {
            return this.xScale(d.x);
          }).attr('cy', (d) => {
            return this.yScaleRight(d.y);
          }).attr('r', 4).attr('fill', lineData.color).attr('stroke', 'white').attr('stroke-width', 2));
        } else {
          results.push(void 0);
        }
      }
      return results;
    }

    addTooltip() {
      var tooltip;
      tooltip = d3.select('body').append('div').attr('class', 'tooltip').style('position', 'absolute').style('padding', '10px').style('background', 'rgba(0, 0, 0, 0.8)').style('color', 'white').style('border-radius', '5px').style('pointer-events', 'none').style('opacity', 0);
      return this.g.selectAll('circle').on('mouseover', function(event, d) {
        tooltip.transition().duration(200).style('opacity', 0.9);
        return tooltip.html(`Time: ${d3.timeFormat('%Y-%m-%d %H:%M')(d.x)}<br/>Value: ${d.y.toFixed(2)}`).style('left', (event.pageX + 10) + 'px').style('top', (event.pageY - 28) + 'px');
      }).on('mouseout', function() {
        return tooltip.transition().duration(500).style('opacity', 0);
      });
    }

    // Method to get the SVG as a string for PDF generation
    getSVGString() {
      var styledSVG, svgNode, svgString;
      // Clone the SVG node to avoid modifying the original
      svgNode = this.svg.node().cloneNode(true);
      
      // Add necessary styles inline for PDF rendering
      svgString = new XMLSerializer().serializeToString(svgNode);
      
      // Add CSS styles that WeasyPrint can understand
      styledSVG = `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="${this.width}" height="${this.height}">
  <defs>
    <style type="text/css"><![CDATA[
      .axis-label { font-size: 12px; font-family: Arial, sans-serif; }
      .x-axis text, .y-axis text { font-size: 11px; font-family: Arial, sans-serif; }
      .x-axis path, .y-axis path, .x-axis line, .y-axis line { 
        fill: none; stroke: #000; shape-rendering: crispEdges; 
      }
      .hline { opacity: 0.7; }
      .line-path { fill: none; stroke-width: 2px; }
      text { fill: #000; }
    ]]></style>
  </defs>
  ${svgNode.innerHTML}
</svg>`;
      return styledSVG;
    }

    
      // Method to render chart and return SVG for PDF
    renderForPDF(rawData) {
      this.plot(rawData);
      return this.getSVGString();
    }

    plot(rawData) {
      var data;
      // Clear previous plot
      this.g.selectAll('*').remove();
      
      // Parse and prepare data
      data = this.parseData(rawData);
      
      // Update scales
      this.updateScales(data);
      
      // Draw components
      this.drawAxes(data);
      this.drawHorizontalLines(data.hlinesLeft, data.hlinesRight);
      this.drawLines(data.linesLeft, data.linesRight);
      
      // Only add tooltips if not generating for PDF
      if (!this.options.forPDF) {
        this.addTooltip();
      }
      
      // Add basic styling
      this.svg.selectAll('.axis-label, .axis-label-left, .axis-label-right').style('font-size', '12px').style('font-family', 'Arial, sans-serif');
      return this.svg.selectAll('.x-axis, .y-axis-left, .y-axis-right').style('font-size', '11px').style('font-family', 'Arial, sans-serif');
    }

  };

  // Usage example:
  // container = '#chart-container'  # CSS selector for container element
  // plotter = new D3LinePlotter(container, { width: 900, height: 500 })
  // plotter.plot(yourDataArray)

  // Export for use in other modules
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = D3LinePlotter;
  } else if (typeof window !== 'undefined') {
    window.D3LinePlotter = D3LinePlotter;
  }

}).call(this);
