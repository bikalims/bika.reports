### Please use this command to compile this file into the parent `js` directory:
    coffee --no-header -w -o ../ -c bika.lims.plotter.coffee
###
class D3LinePlotter
  constructor: (@container, @options = {}) ->
    @width = @options.width || 800
    @height = @options.height || 400
    @margin = @options.margin || { top: 20, right: 70, bottom: 80, left: 50 }
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
    @yScale = d3.scaleLinear().range([@innerHeight, 0])  # Left Y-axis
    @yScaleRight = d3.scaleLinear().range([@innerHeight, 0])  # Right Y-axis
    
    # Initialize line generators
    @line = d3.line()
      .x((d) => @xScale(d.x))
      .y((d) => @yScale(d.y))
      .curve(d3.curveMonotoneX)
    
    @lineRight = d3.line()
      .x((d) => @xScale(d.x))
      .y((d) => @yScaleRight(d.y))
      .curve(d3.curveMonotoneX)

  parseData: (rawData) ->
    parsedData = {
      linesLeft: []
      linesRight: []
      hlinesLeft: []
      hlinesRight: []
      leftAxisTitle: 'Left Axis'
      rightAxisTitle: 'Right Axis'
    }
    
    for series in rawData
      # Determine which Y-axis to use (default to left)
      useRightAxis = series.y_axis is 'right'
      
      # Set axis titles if provided
      if series.left_axis_title
        parsedData.leftAxisTitle = series.left_axis_title
      if series.right_axis_title
        parsedData.rightAxisTitle = series.right_axis_title
      
      if series.plot_type is 'line'
        lineData = {
          color: series.plot_color
          showPoints: series.show_points
          lineStyle: series.line_style || 'solid'  # solid, dashed, dotted
          points: []
        }
        
        for point in series.plot_points
          lineData.points.push({
            x: new Date(point.x.value)
            y: parseFloat(point.y.value)
          })
        
        if useRightAxis
          parsedData.linesRight.push(lineData)
        else
          parsedData.linesLeft.push(lineData)
      
      else if series.plot_type is 'hline'
        hlineData = {
          color: series.plot_color
          y: parseFloat(series.plot_points[0].y.value)
          lineStyle: series.line_style || 'dashed'
        }
        
        if useRightAxis
          parsedData.hlinesRight.push(hlineData)
        else
          parsedData.hlinesLeft.push(hlineData)
    
    return parsedData

  getLineStylePattern: (style) ->
    switch style
      when 'solid' then 'none'
      when 'dashed' then '10,5'
      when 'dotted' then '3,3'
      when 'dash-dot' then '10,5,3,5'
      else 'none'
  updateScales: (data) ->
    # Get all x values from line data
    allXValues = []
    leftYValues = []
    rightYValues = []
    
    # Collect left axis data
    for line in data.linesLeft
      for point in line.points
        allXValues.push(point.x)
        leftYValues.push(point.y)
    
    for hline in data.hlinesLeft
      leftYValues.push(hline.y)
    
    # Collect right axis data
    for line in data.linesRight
      for point in line.points
        allXValues.push(point.x)
        rightYValues.push(point.y)
    
    for hline in data.hlinesRight
      rightYValues.push(hline.y)
    
    # Set X scale domain
    @xScale.domain(d3.extent(allXValues))
    
    # Set Y scale domains with padding
    if leftYValues.length > 0
      leftExtent = d3.extent(leftYValues)
      leftRange = leftExtent[1] - leftExtent[0]
      leftPadding = leftRange * 0.1
      @yScale.domain([leftExtent[0] - leftPadding, leftExtent[1] + leftPadding])
    
    if rightYValues.length > 0
      rightExtent = d3.extent(rightYValues)
      rightRange = rightExtent[1] - rightExtent[0]
      rightPadding = rightRange * 0.1
      @yScaleRight.domain([rightExtent[0] - rightPadding, rightExtent[1] + rightPadding])

  drawAxes: (data) ->
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
    
    # Left Y Axis (integers)
    @g.append('g')
      .attr('class', 'y-axis-left')
      .call(d3.axisLeft(@yScale).tickFormat(d3.format('.1f')))
    
    # Right Y Axis (floats) - only if we have right-axis data
    if @yScaleRight.domain()[0] isnt @yScaleRight.domain()[1]
      @g.append('g')
        .attr('class', 'y-axis-right')
        .attr('transform', "translate(#{@innerWidth},0)")
        .call(d3.axisRight(@yScaleRight).tickFormat(d3.format('.1f')))
    
    # Add axis labels
    @g.append('text')
      .attr('class', 'axis-label-left')
      .attr('transform', 'rotate(-90)')
      .attr('y', 0 - @margin.left)
      .attr('x', 0 - (@innerHeight / 2))
      .attr('dy', '1em')
      .style('text-anchor', 'middle')
      .text(data.leftAxisTitle)
    
    # Right axis label (only if we have right-axis data)
    if @yScaleRight.domain()[0] isnt @yScaleRight.domain()[1]
      @g.append('text')
        .attr('class', 'axis-label-right')
        .attr('transform', 'rotate(-90)')
        .attr('y', @innerWidth + @margin.right - 10)
        .attr('x', 0 - (@innerHeight / 2))
        .attr('dy', '1em')
        .style('text-anchor', 'middle')
        .text(data.rightAxisTitle)
    
    @g.append('text')
      .attr('class', 'axis-label')
      .attr('transform', "translate(#{@innerWidth / 2}, #{@innerHeight + @margin.bottom})")
      .style('text-anchor', 'middle')
      .text('Time')

  drawHorizontalLines: (hlinesLeft, hlinesRight) ->
    # Left axis horizontal lines
    @g.selectAll('.hline-left')
      .data(hlinesLeft)
      .enter()
      .append('line')
      .attr('class', 'hline-left')
      .attr('x1', 0)
      .attr('x2', @innerWidth)
      .attr('y1', (d) => @yScale(d.y))
      .attr('y2', (d) => @yScale(d.y))
      .attr('stroke', (d) -> d.color)
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', (d) => @getLineStylePattern(d.lineStyle))
      .attr('opacity', 0.7)
    
    # Right axis horizontal lines
    @g.selectAll('.hline-right')
      .data(hlinesRight)
      .enter()
      .append('line')
      .attr('class', 'hline-right')
      .attr('x1', 0)
      .attr('x2', @innerWidth)
      .attr('y1', (d) => @yScaleRight(d.y))
      .attr('y2', (d) => @yScaleRight(d.y))
      .attr('stroke', (d) -> d.color)
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', (d) => @getLineStylePattern(d.lineStyle))
      .attr('opacity', 0.7)

  drawLines: (linesLeft, linesRight) ->
    # Draw left axis line paths
    @g.selectAll('.line-path-left')
      .data(linesLeft)
      .enter()
      .append('path')
      .attr('class', 'line-path-left')
      .attr('d', (d) => @line(d.points))
      .attr('fill', 'none')
      .attr('stroke', (d) -> d.color)
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', (d) => @getLineStylePattern(d.lineStyle))
    
    # Draw right axis line paths
    @g.selectAll('.line-path-right')
      .data(linesRight)
      .enter()
      .append('path')
      .attr('class', 'line-path-right')
      .attr('d', (d) => @lineRight(d.points))
      .attr('fill', 'none')
      .attr('stroke', (d) -> d.color)
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', (d) => @getLineStylePattern(d.lineStyle))
    
    # Draw points for left axis lines
    for lineData, i in linesLeft
      if lineData.showPoints
        @g.selectAll(".point-left-#{i}")
          .data(lineData.points)
          .enter()
          .append('circle')
          .attr('class', "point-left-#{i}")
          .attr('cx', (d) => @xScale(d.x))
          .attr('cy', (d) => @yScale(d.y))
          .attr('r', 4)
          .attr('fill', lineData.color)
          .attr('stroke', 'white')
          .attr('stroke-width', 2)
    
    # Draw points for right axis lines
    for lineData, i in linesRight
      if lineData.showPoints
        @g.selectAll(".point-right-#{i}")
          .data(lineData.points)
          .enter()
          .append('circle')
          .attr('class', "point-right-#{i}")
          .attr('cx', (d) => @xScale(d.x))
          .attr('cy', (d) => @yScaleRight(d.y))
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
    @drawAxes(data)
    @drawHorizontalLines(data.hlinesLeft, data.hlinesRight)
    @drawLines(data.linesLeft, data.linesRight)
    
    # Only add tooltips if not generating for PDF
    unless @options.forPDF
      @addTooltip()
    
    # Add basic styling
    @svg.selectAll('.axis-label, .axis-label-left, .axis-label-right')
      .style('font-size', '12px')
      .style('font-family', 'Arial, sans-serif')
    
    @svg.selectAll('.x-axis, .y-axis-left, .y-axis-right')
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
