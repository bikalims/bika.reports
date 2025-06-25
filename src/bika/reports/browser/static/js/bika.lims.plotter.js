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
        right: 20,
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
      this.yScale = d3.scaleLinear().range([this.innerHeight, 0]);
      
      // Initialize line generator
      this.line = d3.line().x((d) => {
        return this.xScale(d.x);
      }).y((d) => {
        return this.yScale(d.y);
      }).curve(d3.curveMonotoneX);
    }

    parseData(rawData) {
      var hlineData, j, k, len, len1, lineData, parsedData, point, ref, series;
      parsedData = {
        lines: [],
        hlines: []
      };
      for (j = 0, len = rawData.length; j < len; j++) {
        series = rawData[j];
        if (series.plot_type === 'line') {
          lineData = {
            color: series.plot_color,
            showPoints: series.show_points,
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
          parsedData.lines.push(lineData);
        } else if (series.plot_type === 'hline') {
          hlineData = {
            color: series.plot_color,
            y: parseFloat(series.plot_points[0].y.value)
          };
          parsedData.hlines.push(hlineData);
        }
      }
      return parsedData;
    }

    updateScales(data) {
      var allXValues, allYValues, hline, j, k, l, len, len1, len2, line, point, ref, ref1, ref2, yExtent, yPadding, yRange;
      // Get all x values from line data
      allXValues = [];
      allYValues = [];
      ref = data.lines;
      for (j = 0, len = ref.length; j < len; j++) {
        line = ref[j];
        ref1 = line.points;
        for (k = 0, len1 = ref1.length; k < len1; k++) {
          point = ref1[k];
          allXValues.push(point.x);
          allYValues.push(point.y);
        }
      }
      ref2 = data.hlines;
      
      // Add horizontal line y values
      for (l = 0, len2 = ref2.length; l < len2; l++) {
        hline = ref2[l];
        allYValues.push(hline.y);
      }
      this.xScale.domain(d3.extent(allXValues));
      
      // Add padding to Y domain for better spacing
      yExtent = d3.extent(allYValues);
      yRange = yExtent[1] - yExtent[0];
      yPadding = yRange * 0.1; // 10% padding on top and bottom
      return this.yScale.domain([yExtent[0] - yPadding, yExtent[1] + yPadding]);
    }

    drawAxes() {
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
      
      // Y Axis
      this.g.append('g').attr('class', 'y-axis').call(d3.axisLeft(this.yScale));
      
      // Add axis labels
      this.g.append('text').attr('class', 'axis-label').attr('transform', 'rotate(-90)').attr('y', 0 - this.margin.left).attr('x', 0 - (this.innerHeight / 2)).attr('dy', '1em').style('text-anchor', 'middle').text('Value');
      return this.g.append('text').attr('class', 'axis-label').attr('transform', `translate(${this.innerWidth / 2}, ${this.innerHeight + this.margin.bottom})`).style('text-anchor', 'middle').text('Time');
    }

    drawHorizontalLines(hlines) {
      return this.g.selectAll('.hline').data(hlines).enter().append('line').attr('class', 'hline').attr('x1', 0).attr('x2', this.innerWidth).attr('y1', (d) => {
        return this.yScale(d.y);
      }).attr('y2', (d) => {
        return this.yScale(d.y);
      }).attr('stroke', function(d) {
        return d.color;
      }).attr('stroke-width', 2).attr('stroke-dasharray', '5,5').attr('opacity', 0.7);
    }

    drawLines(lines) {
      var i, j, len, lineData, results;
      // Draw line paths
      this.g.selectAll('.line-path').data(lines).enter().append('path').attr('class', 'line-path').attr('d', (d) => {
        return this.line(d.points);
      }).attr('fill', 'none').attr('stroke', function(d) {
        return d.color;
      }).attr('stroke-width', 2);

      // Draw points if requested
      results = [];
      for (i = j = 0, len = lines.length; j < len; i = ++j) {
        lineData = lines[i];
        if (lineData.showPoints) {
          results.push(this.g.selectAll(`.point-${i}`).data(lineData.points).enter().append('circle').attr('class', `point-${i}`).attr('cx', (d) => {
            return this.xScale(d.x);
          }).attr('cy', (d) => {
            return this.yScale(d.y);
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
      this.drawAxes();
      this.drawHorizontalLines(data.hlines);
      this.drawLines(data.lines);
      
      // Only add tooltips if not generating for PDF
      if (!this.options.forPDF) {
        this.addTooltip();
      }
      
      // Add basic styling
      this.svg.selectAll('.axis-label').style('font-size', '12px').style('font-family', 'Arial, sans-serif');
      return this.svg.selectAll('.x-axis, .y-axis').style('font-size', '11px').style('font-family', 'Arial, sans-serif');
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
