### Please use this command to compile this file into the parent `js` directory:
    coffee --no-header -w -o ../ -c bika.lims.reports.coffee
###

class window.ReportFolderView

  load: =>
    console.debug "ReportFolderView::load"

    # initialize toggle anchors
    @bind_eventhandler()

    # initialize api
    @api = new ReportsAPI()

    # Use requestAnimationFrame to wait for DOM painting
    requestAnimationFrame =>
      @initialize_plugins()

  ### INITIALIZERS ###

  bind_eventhandler: =>
    ###
     * Binds callbacks on elements
    ###
    console.debug "ReportFolderView::bind_eventhandler"

    # When the anchor for a given report is selected, display the report form
    $("body").on "click", "a[id$='_selector']", @on_toggle_change
    

  initialize_plugins: =>
    console.log "TomSelect is a " + typeof TomSelect
    if typeof TomSelect is "undefined"
      console.warn "TomSelect not ready, retrying..."
      setTimeout @initialize_plugins, 50
      return

    @tomselects = {}
    $(".tomsel").each (i, el) =>
      select_el = el.childNodes[0].childNodes[3]
      try
        ts = new TomSelect(select_el,
          create: false
          allowEmptyOption: true
          placeholder: "Choose an option"
          sortField: {
            field: "text"
            direction: "asc"
          }
        )
        @tomselects[select_el.id] = ts
        console.debug "Wrapper: " + ts.wrapper
        console.debug "Input: " + ts.input
        console.debug "TomSelect init worked " + select_el
      catch err
        console.error "TomSelect init failed:", err

    # When the dropdown is changed for a given select, update dependant dropdown
    # $("#ClientUID").on "change", "select", @on_dropdown_change
    $("body").on "change", "select", @on_dropdown_change

    console.log "TomSelect initialised"

  on_toggle_change: (event) =>
    ###*
     * Event handler when the toggle anchor is clicked
    ###
    console.debug "°°° ReportFolderView::on_toggle_change with" + event + " °°°"

    event.preventDefault()
    $(".criteria").toggle false
    div_id = event.currentTarget.id.split("_selector")[0]
    $("[id='"+div_id+"']").toggle true

  call_command: (command, limit=1000) =>
    if limit
      command += '&limit=' + limit
    console.log "call_command: " + command
    result = this.api.get_json command, method: "GET"
    return result

  populate_dropdown: (el_name, items, clear=true, add_empty=false) =>
    console.log "populate_dropdown: " + el_name
    # eransform to [{value: "foo", text: "Foo"}, ...]
    data = []
    for item in items
      data.push {value: item['uid'], text: item['title']}

    # Assume data.options is [{value: "foo", text: "Foo"}, ...]
    ts = @tomselects[el_name]
    if ts?
      ts.clearOptions()
      for opt in data
        ts.addOption(opt)
      ts.refreshOptions(false)
    else
      console.error 'populate_dropdown: missing TS element ' + el_name + ' in ' + @tomselects

    # # Empty select
    # $el = $(el_name)
    # 
    # # Empty select if specified
    # if clear
    #   $el.empty()

    # # Add new options
    # if add_empty
    #   $('<option>').val('').text('').appendTo($el)  # Empty option

    # # Add new options
    # for item in sorted_items
    #   $('<option>').val(item.uid).text(item.title).appendTo($el)

  get_object_values: (fieldname, items) =>
    result = []
    for item in items
      if item.hasOwnProperty(fieldname)
        for val in item[fieldname]
          result.push val['uid']
    debugger;
    return result
        
  client_selected: (selected_client) =>
    console.log 'Got ClientUID: ' + selected_client
    me = this
    if selected_client
      command = 'search?portal_type=SamplePoint&getClientUID=&getClientUID=' + selected_client
    else
      command = 'search?portal_type=SamplePoint&getClientUID='
    # Get items
    result = me.call_command(command)
    result.then (data) ->
      console.debug('Items returned: ' + data.items.length)
      me.populate_dropdown('SamplePointUID', data.items, clear=true, add_empty=true)
      
      command = 'search?portal_type=SampleType'
      result = me.call_command(command)
      result.then (data) ->
         console.debug('Items returned: ' + data.items.length)
         me.populate_dropdown('SampleTypeUID', data.items, clear=true, add_empty=true)

         command = 'search?portal_type=AnalysisSpec'
         result = me.call_command(command)
         result.then (data) ->
            console.debug('Items returned: ' + data.items.length)
            me.populate_dropdown('analysis_spec', data.items, clear=true, add_empty=true)

            command = 'search?portal_type=AnalysisService'
            result = me.call_command(command)
            result.then (data) ->
               console.debug('Items returned: ' + data.items.length)
               me.populate_dropdown('ServiceUID', data.items, clear=true, add_empty=false)
               me.populate_dropdown('SecondServiceUID', data.items, clear=true, add_empty=true)

  sample_point_selected: (selected_sample_point) =>
    console.log 'Got SamplePointUID" ' + selected_sample_point
    me = this
    if selected_sample_point
      command = 'samplepoint/' + selected_sample_point
   
      # Get samplepoint
      result = me.call_command(command, limit=0)
      result.then (data) ->
         console.debug('Items returned: ' + data.items.length)
         command = 'search?portal_type=SampleType'
         sample_type_uids = me.get_object_values('sample_types', data.items)
         if sample_type_uids
           for sample_type_uid in sample_type_uids
             command += '&UID=' + sample_type_uid
       
         # Get items
         result = me.call_command(command)
         result.then (data) ->
            console.debug('Items returned: ' + data.items.length)
            me.populate_dropdown('SampleTypeUID', data.items, clear=true, add_empty=true)

            command = 'search?portal_type=AnalysisSpec'
            result = me.call_command(command)
            result.then (data) ->
               console.debug('Items returned: ' + data.items.length)
               me.populate_dropdown('analysis_spec', data.items, clear=true, add_empty=true)

               command = 'search?portal_type=AnalysisService'
               result = me.call_command(command)
               result.then (data) ->
                  console.debug('Items returned: ' + data.items.length)
                  me.populate_dropdown('ServiceUID', data.items, clear=true, add_empty=false)
                  me.populate_dropdown('SecondServiceUID', data.items, clear=true, add_empty=true)


  sample_type_selected: (selected_sample_type) =>
    console.log 'Got SampleTypeUID" ' + selected_sample_type
    me = this
    if selected_sample_type
       command = 'search?portal_type=AnalysisSpec&sampletype_uid=' + selected_sample_type
     else
       command = 'search?portal_type=AnalysisSpec'
     
     # Get items
     result = me.call_command(command)
     result.then (data) ->
        console.debug('Items returned: ' + data.items.length)
        me.populate_dropdown('analysis_spec', data.items, clear=true, add_empty=true)

        command = 'search?portal_type=AnalysisService'
        result = me.call_command(command)
        result.then (data) ->
           console.debug('Items returned: ' + data.items.length)
           me.populate_dropdown('ServiceUID', data.items, clear=true, add_empty=false)
           me.populate_dropdown('SecondServiceUID', data.items, clear=true, add_empty=true)

  analysis_spec_selected: (selected_analysis_spec) =>
    console.log 'Got AnalysisSpec" ' + selected_analysis_spec
    me = this
    if selected_analysis_spec
      command = 'analysisspec/' + selected_analysis_spec
      result = me.call_command(command, limit=0)
      result.then (data) ->
         service_uids = me.get_object_values('ResultsRange', data.items)

         command = 'search?portal_type=AnalysisService'
         if service_uids
           for service_uid in service_uids
             command += '&UID=' + service_uid
   
           # Get Services
           result = me.call_command(command)
           result.then (data) ->
              console.debug('Items returned: ' + data.items.length)
              me.populate_dropdown('ServiceUID', data.items, clear=true, add_empty=false)
              me.populate_dropdown('SecondServiceUID', data.items, clear=true, add_empty=true)
    else
      # Get Services
      command = 'search?portal_type=AnalysisService'
      result = me.call_command(command)
      result.then (data) ->
         console.debug('Items returned: ' + data.items.length)
         me.populate_dropdown('ServiceUID', data.items, clear=true, add_empty=false)
         me.populate_dropdown('SecondServiceUID', data.items, clear=true, add_empty=true)


  on_dropdown_change: (e) =>
    ###*
     * Event handler when dropdown changed
    ###
    console.debug "°°° ReportFolderView::on_dropdown_change on e " + e.id + " °°°"
    if e.currentTarget
      $el = $(e.currentTarget)
    else
      $el = $(e)
    console.log "°°° ReportFolderView::on_dropdown_change on target" + $el.id + " °°°"
    outer_parent = $el.closest('.update_dropdown')
    if not $el.closest('.update_dropdown').length
      console.log 'element ' + $el + ' not closest to update_dropdown'
      return

    console.log 'update_dropdown: ' + e.target.id
    e.preventDefault()

    if e.target.id == 'ClientUID'
      console.log 'ClientUID selected'
      selected_client = $(e.target).val()
      @client_selected selected_client

    if e.target.id == 'SamplePointUID'
      selected_sample_point = $(e.target).val()
      console.log 'SamplePointUID selected: ' + selected_sample_point
      @sample_point_selected selected_sample_point

    if e.target.id == 'SampleTypeUID'
      console.log 'SampleTypeUID selected'
      selected_sample_type = $(e.target).val()
      @sample_type_selected selected_sample_type

    if e.target.id == 'analysis_spec'
      console.log 'analysis_spec selected'
      selected_analysis_spec = $(e.target).val()
      @analysis_spec_selected selected_analysis_spec

    console.log 'on_dropdown_change complete'



obj = new window["ReportFolderView"]()
obj.load()
