
class BikaPlot 

  ###*
   * Plot an chart in Bika.Reports
   *
  ###
  constructor: (config) ->
    @props = config
    # console.log('constructor complete')

  ###
   * Calculate Y range
  ###
  get_Y_range: (minY, maxY) ->
    diffY = maxY - minY
    interval = 0
    if diffY > 70
      interval = 10
    else if diffY > 50
      interval = 5
    else if diffY > 20
      interval = 2
    else if diffY > 10
      interval = 1

    if interval > 0
      minTicks = minY - (minY % interval) + interval
      maxTicks = maxY + (maxY % interval) + interval
      y_range = d3.range(minTicks, maxTicks, interval)
    else
      y_range = d3.range(minY, maxY)

    # console.log "Y Axis: min: ", minY, " max: ", maxY, " diffY: ", diffY, " interval: ", interval
    y_range

  ###
   * Converts the string value to an array
  ###
  to_matrix: (data) ->

    # Map each inner list to an object
    matrix = data.map (sublist) ->
      row = sublist.map (item, idx) ->
        if 'plot' of item[0]
          item['x'] = item[0]['plot']

        if 'plot' of item[1]
          item['y'] = item[1]['plot'] % 100
        item
      row


    # # Format values
    # matrix.map (row) ->
    #     console.log(row)
    #     headers.forEach (header, index) ->
    #       if index = 0
    #         row[header] = row[header]
    #       else
    #         row[header] = parseFloat(row[header])

    matrix


  getLineConfigs = (count) ->
    configs = [
      {symbol: d3.symbolStar, dash: ""}
      {symbol: d3.symbolSquare, dash: ""}
      {symbol: d3.symbolTriangle, dash: ""}
      {symbol: d3.symbolDiamond, dash: ""}
      {symbol: d3.symbolCross, dash: ""}
    ]
    configs.slice(0, count)

  # Create symbol generator
  symbolGenerator = d3.symbol().size(48)  # Adjust size as needed

  ###
   * Inputs table builder. Generates a table of  inputs as matrix
  ###
  build_plot: (container)->
    console.log "BikaPlot::build_plot: entered with ", container
    try
      console.log("Data being used for rendering:", this.props.datalines)  # Log the data

      if this.props.datalines == ""
        console.log "BikaPlot::build_plot: exit because no datalines"
        container.current.appendChild([])
        return

      # Get datasets
      # headers = this.props.formats.col_heads
      # col_types = columns.map (i) -> i.ColumnType
      # col_colors = columns.map (i) -> i.ColumnColor
      data = @to_matrix(this.props.datalines)

      # line_configs = getLineConfigs(headers.length - 1)

      # Set up dimensions
      margin = {top: 40, right: 80, bottom: 50, left: 60}
      width = 700 - margin.left - margin.right
      height = 400 - margin.top - margin.bottom + 50

      # Set up Y scale
      minX = d3.min(data.flatMap((row) -> row.map((item) -> item['x'])))
      maxX = d3.max(data.flatMap((row) -> row.map((item) -> item['x'])))
      xScale = d3.scaleLinear()
        .domain([Math.floor(minX), Math.ceil(maxX)])  # Trim domain to just cover data range
        .range([0, width])

      # Set up Y scale with trimmed domain
      absoluteMinY = d3.min(data.flatMap((row) -> row.map((item) -> item['y'])))
      minY_factor = 0.05; # 20%
      minY = absoluteMinY - absoluteMinY * minY_factor;
      console.info 'minY: ' + minY

      maxY = d3.max(data.flatMap((row) -> row.map((item) -> item['y'])))
      console.info 'maxY: ' + maxY

      yScale = d3.scaleLinear()
        .domain([Math.floor(minY), Math.ceil(maxY)])  # Trim domain to just cover data range
        .range([height, 0])

      # Create SVG container
      svg = d3.select(container)
        .append('svg')
        .attr("id", "bika-plot-svg")  # Add unique ID
        .style("height", "#{height+140}px")

      # Remove any previous SVG content
      svg.selectAll('*').remove()

      svg = svg
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .attr('xmlns', 'http://www.w3.org/2000/svg')
        .append("g")
        .attr("transform", "translate(#{margin.left},#{margin.top})")

      # Graph title
      svg.append("text")
        .attr("x", width / 2)
        .attr("y", -margin.top / 2)
        .attr("text-anchor", "middle")
        .style("font-size", "16px")
        .style("font-weight", "bold")
        .text(this.props.headings.header)

      # # Graph sub title
      # svg.append("text")
      #   .attr("x", width / 2)
      #   .attr("y", -margin.top / 2)
      #   .attr("text-anchor", "middle")
      #   .style("font-size", "10px")
      #   .style("font-weight", "bold")
      #   .text(this.props.headings.subheader)

      # X-axis
      svg.append("g")
        .attr("transform", "translate(0,#{height})")
        .call(d3.axisBottom(xScale))

      # # X-axis label
      # svg.append("text")
      #   .attr("x", width / 2)
      #   .attr("y", height + margin.bottom - 10)
      #   .attr("text-anchor", "middle")
      #   .style("font-size", "12px")
      #   .text(this.props.item.time_series_graph_xaxis)

      # Y-axis
      y_range = @get_Y_range(minY, maxY)
      console.info 'Y Range: ' + y_range
      yAxis = d3.axisLeft(yScale)
        .tickValues(y_range)
        .tickSize(-width)  # Extend ticks across the chart width

      # # Y-axis label
      # svg.append("text")
      #   .attr("transform", "rotate(-90)")
      #   .attr("x", -height / 2)
      #   .attr("y", -margin.left + 15)
      #   .attr("text-anchor", "middle")
      #   .style("font-size", "12px")
      #   .text(this.props.item.time_series_graph_yaxis)

      # Add horizontal grid lines
      svg.append("g")
          .attr("class", "grid horizontal")
          .attr("transform", "translate(0, 0)")
          .call(yAxis)
          .selectAll("line")
          .style("stroke", "#999")  # Lighter gray
          .style("opacity", 0.4)       # Adjust transparency


      xAxis = d3.axisBottom(xScale)
          .tickSize(-height)  # Extend ticks across the chart height
          .tickFormat("")     # Remove tick labels
          .tickValues([10, 20, 30, 40, 50])

      # Add vertical grid lines
      svg.append("g")
        .attr("class", "grid vertical")
        .attr("transform", "translate(0, #{height})")
        .call(xAxis)
        .selectAll("line")
        .style("stroke", "#999")  # Lighter gray
        .style("stroke-dasharray", "2,2")
        .style("opacity", 0.8)       # Adjust transparency

      # Draw axes
      svg.append("g")
        .attr("transform", "translate(0,#{height})")
        .call(d3.axisBottom(xScale))

      # # Get interpolation
      # interp = this.props.item.time_series_graph_interpolation
      # console.info interp 
      # curve_val = d3[interp]

      data.forEach((row, idx, full) ->
        console.info "Main loop: row: " + row.length

        row.forEach((item) ->
          console.info "Main loop: item: x=" + item['x'] + " y=" + item['y']
        )

        # Line generator
        lineGen = d3.line()
          .x((d) ->
            xScale(d['x'])
          )
          .y((d) ->
            yScale(d['y'])
          )

        svg.append("path")
          .datum(row)
          .attr("fill", "none")
          .attr("stroke-width", 2)
          .attr("stroke", 'red')
          # .attr("stroke-dasharray", line_configs[idx].dash)
          .attr("d", lineGen)

        # Add data points with different symbols
        svg.selectAll(".symbol-#{idx}")
          .data(row) # Use filtered data
          .enter().append("path")
          # .attr("class", "symbol symbol-#{idx}")
          .attr("d", d3.symbolSquare)
          .attr("transform", (d) ->
            # Ensure valid x and y before applying transform
            xVal = d['x']
            yVal = d['y']
            if not isNaN(xVal) and not isNaN(yVal)
              "translate(#{xScale(xVal)}, #{yScale(yVal)})"
            else
              null # Skip invalid points
          )
          .style("fill", "black")
      )

      # Add legend
      legend = svg.append("g")
        .attr("class", "legend")
        .attr("transform", "translate(50, #{height + 50})")  # Move legend below the graph

      # # Add legend items
      # legendItems = legend.selectAll("g")
      #   .data(headers.slice(1))
      #   .enter().append("g")
      #   .attr("transform", (d, i) ->
      #     xOffset = parseFloat((i % Math.floor(width / 100)) * 100)  # Horizontal spacing
      #     yOffset = parseFloat(Math.floor(i / Math.floor(width / 100)) * 20)  # Vertical spacing
      #     "translate(#{xOffset}, #{yOffset})"
      #   )

      # # Add legend color symbols
      # legendItems.append("path")
      #   .attr("d", (d, i) ->
      #     d3.symbol()
      #       # .type(line_configs[i].symbol)
      #       .size(100)()
      #   )
      #   .attr("transform", "translate(9, 9)")  # Center the symbol within the legend item
      #   # .style("fill", (d, i) -> col_colors[i+1])

      # # Add legend text
      # legendItems.append("text")
      #   .attr("x", 24)
      #   .attr("y", 9)
      #   .attr("dy", "0.35em")
      #   .style("font-size", "12px")
      #   .text((d) -> d)

      console.log "BikaPlot::build_plot: ended"

    catch error
      console.error("Error in build_plot:", error)

window.BikaPlot = BikaPlot
