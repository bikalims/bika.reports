class D3LinePlotter
  constructor: (@container, @options = {}) ->
    @width = @options.width || 800
    @height = @options.height || 400
    @margin = @options.margin || { top: 20, right: 20, bottom: 80, left: 50 }
    @innerWidth = @width - @margin.left - @margin.right
    @innerHeight = @height - @margin.top - @margin.bottom
    
    # Initialize SVG
    @svg = d3.select(@container)
      .append('svg')
      .attr('width', @width)
      .attr('height', @height)
    
    @g = @svg.append('g')
      .attr('transform', "translate(#{@margin.left},#{@margin.top})")
    
    # Initialize scales
    @xScale = d3.scaleTime().range([0, @innerWidth])
    @yScale = d3.scaleLinear().range([@innerHeight, 0])
    
    # Initialize line generator
    @line = d3.line()
      .x((d) => @xScale(d.x))
      .y((d) => @yScale(d.y))
      .curve(d3.curveMonotoneX)

  parseData: (rawData) ->
    parsedData = {
      lines: []
      hlines: []
    }
    
    for series in rawData
      if series.plot_type is 'line'
        lineData = {
          color: series.plot_color
          showPoints: series.show_points
          points: []
        }
        
        for point in series.plot_points
          lineData.points.push({
            x: new Date(point.x.value)
            y: parseFloat(point.y.value)
          })
        
        parsedData.lines.push(lineData)
      
      else if series.plot_type is 'hline'
        hlineData = {
          color: series.plot_color
          y: parseFloat(series.plot_points[0].y.value)
        }
        
        parsedData.hlines.push(hlineData)
    
    return parsedData

  updateScales: (data) ->
    # Get all x values from line data
    allXValues = []
    allYValues = []
    
    for line in data.lines
      for point in line.points
        allXValues.push(point.x)
        allYValues.push(point.y)
    
    # Add horizontal line y values
    for hline in data.hlines
      allYValues.push(hline.y)
    
    @xScale.domain(d3.extent(allXValues))
    
    # Add padding to Y domain for better spacing
    yExtent = d3.extent(allYValues)
    yRange = yExtent[1] - yExtent[0]
    yPadding = yRange * 0.1  # 10% padding on top and bottom
    
    @yScale.domain([yExtent[0] - yPadding, yExtent[1] + yPadding])

  drawAxes: ->
    # X Axis with better date/time formatting
    timeRange = @xScale.domain()
    timeDiff = timeRange[1] - timeRange[0]
    
    # Choose appropriate format based on time span
    if timeDiff < 24 * 60 * 60 * 1000  # Less than 24 hours
      tickFormat = d3.timeFormat('%m/%d %H:%M')
      tickCount = Math.min(8, Math.max(3, Math.floor(@innerWidth / 100)))
    else if timeDiff < 7 * 24 * 60 * 60 * 1000  # Less than 7 days
      tickFormat = d3.timeFormat('%m/%d %H:%M')
      tickCount = Math.min(10, Math.max(4, Math.floor(@innerWidth / 80)))
    else
      tickFormat = d3.timeFormat('%Y-%m-%d')
      tickCount = Math.min(8, Math.max(3, Math.floor(@innerWidth / 120)))
    
    @g.append('g')
      .attr('class', 'x-axis')
      .attr('transform', "translate(0,#{@innerHeight})")
      .call(d3.axisBottom(@xScale)
        .tickFormat(tickFormat)
        .ticks(tickCount))
    
    # Rotate x-axis labels for better readability
    @g.selectAll('.x-axis text')
      .style('text-anchor', 'end')
      .attr('dx', '-.8em')
      .attr('dy', '.15em')
      .attr('transform', 'rotate(-45)')
    
    # Y Axis
    @g.append('g')
      .attr('class', 'y-axis')
      .call(d3.axisLeft(@yScale))
    
    # Add axis labels
    @g.append('text')
      .attr('class', 'axis-label')
      .attr('transform', 'rotate(-90)')
      .attr('y', 0 - @margin.left)
      .attr('x', 0 - (@innerHeight / 2))
      .attr('dy', '1em')
      .style('text-anchor', 'middle')
      .text('Value')
    
    @g.append('text')
      .attr('class', 'axis-label')
      .attr('transform', "translate(#{@innerWidth / 2}, #{@innerHeight + @margin.bottom})")
      .style('text-anchor', 'middle')
      .text('Time')

  drawHorizontalLines: (hlines) ->
    @g.selectAll('.hline')
      .data(hlines)
      .enter()
      .append('line')
      .attr('class', 'hline')
      .attr('x1', 0)
      .attr('x2', @innerWidth)
      .attr('y1', (d) => @yScale(d.y))
      .attr('y2', (d) => @yScale(d.y))
      .attr('stroke', (d) -> d.color)
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', '5,5')
      .attr('opacity', 0.7)

  drawLines: (lines) ->
    # Draw line paths
    @g.selectAll('.line-path')
      .data(lines)
      .enter()
      .append('path')
      .attr('class', 'line-path')
      .attr('d', (d) => @line(d.points))
      .attr('fill', 'none')
      .attr('stroke', (d) -> d.color)
      .attr('stroke-width', 2)
    
    # Draw points if requested
    for lineData, i in lines
      if lineData.showPoints
        @g.selectAll(".point-#{i}")
          .data(lineData.points)
          .enter()
          .append('circle')
          .attr('class', "point-#{i}")
          .attr('cx', (d) => @xScale(d.x))
          .attr('cy', (d) => @yScale(d.y))
          .attr('r', 4)
          .attr('fill', lineData.color)
          .attr('stroke', 'white')
          .attr('stroke-width', 2)

  addTooltip: ->
    tooltip = d3.select('body').append('div')
      .attr('class', 'tooltip')
      .style('position', 'absolute')
      .style('padding', '10px')
      .style('background', 'rgba(0, 0, 0, 0.8)')
      .style('color', 'white')
      .style('border-radius', '5px')
      .style('pointer-events', 'none')
      .style('opacity', 0)
    
    @g.selectAll('circle')
      .on('mouseover', (event, d) ->
        tooltip.transition()
          .duration(200)
          .style('opacity', 0.9)
        tooltip.html("Time: #{d3.timeFormat('%Y-%m-%d %H:%M')(d.x)}<br/>Value: #{d.y.toFixed(2)}")
          .style('left', (event.pageX + 10) + 'px')
          .style('top', (event.pageY - 28) + 'px')
      )
      .on('mouseout', ->
        tooltip.transition()
          .duration(500)
          .style('opacity', 0)
      )

  # Method to get the SVG as a string for PDF generation
  getSVGString: ->
    # Clone the SVG node to avoid modifying the original
    svgNode = @svg.node().cloneNode(true)
    
    # Add necessary styles inline for PDF rendering
    svgString = new XMLSerializer().serializeToString(svgNode)
    
    # Add CSS styles that WeasyPrint can understand
    styledSVG = """
    <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="#{@width}" height="#{@height}">
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
      #{svgNode.innerHTML}
    </svg>
    """
    
    return styledSVG
  
  # Method to render chart and return SVG for PDF
  renderForPDF: (rawData) ->
    @plot(rawData)
    return @getSVGString()

  plot: (rawData) ->
    # Clear previous plot
    @g.selectAll('*').remove()
    
    # Parse and prepare data
    data = @parseData(rawData)
    
    # Update scales
    @updateScales(data)
    
    # Draw components
    @drawAxes()
    @drawHorizontalLines(data.hlines)
    @drawLines(data.lines)
    
    # Only add tooltips if not generating for PDF
    unless @options.forPDF
      @addTooltip()
    
    # Add basic styling
    @svg.selectAll('.axis-label')
      .style('font-size', '12px')
      .style('font-family', 'Arial, sans-serif')
    
    @svg.selectAll('.x-axis, .y-axis')
      .style('font-size', '11px')
      .style('font-family', 'Arial, sans-serif')

# Usage example:
# container = '#chart-container'  # CSS selector for container element
# plotter = new D3LinePlotter(container, { width: 900, height: 500 })
# plotter.plot(yourDataArray)

# Export for use in other modules
if typeof module isnt 'undefined' and module.exports
  module.exports = D3LinePlotter
else if typeof window isnt 'undefined'
  window.D3LinePlotter = D3LinePlotter
