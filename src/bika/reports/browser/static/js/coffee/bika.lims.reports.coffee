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


  ### INITIALIZERS ###

  bind_eventhandler: =>
    ###
     * Binds callbacks on elements
    ###
    console.debug "ReportFolderView::bind_eventhandler"

    # When the anchor for a given report is selected, display the report form
    $("body").on "click", "a[id$='_selector']", @on_toggle_change
    # When the dropdown is changed for a given select, update dependant dropdown
    $("body").on "change", "select", @on_dropdown_change


  on_toggle_change: (event) =>
    ###*
     * Event handler when the toggle anchor is clicked
    ###
    console.debug "°°° ReportFolderView::on_toggle_change °°°"

    event.preventDefault()
    $(".criteria").toggle false
    div_id = event.currentTarget.id.split("_selector")[0]
    $("[id='"+div_id+"']").toggle true

  populate_dropdown: (el_name, items, clear=true, add_empty=false) =>
      # Empty select
      $el = $(el_name)
      
      # Empty select if specified
      if clear
        $el.empty()

      # Add new options
      if add_empty
        $('<option>').val('').text('').appendTo($el)  # Empty option

      # Add new options
      for item in items
        $('<option>').val(item.uid).text(item.title).appendTo($el)

  get_object_values: (fieldname, items) =>
    result = []
    for item in items
      if item.hasOwnProperty(fieldname)
        for val in item[fieldname]
          result.push val['uid']
    return result
        
  client_selected: (selected_client) =>
    console.log 'Got ClientUID: ' + selected_client
    me = this
    if selected_client
      command = 'search?portal_type=SamplePoint&getClientUID=&getClientUID=' + selected_client
    else
      command = 'search?portal_type=SamplePoint&getClientUID='
    # Get items
    result = me.api.get_json command, method: "GET"
    result.then (data) ->
      console.log('Items returned: ' + data.items.length)
      me.populate_dropdown('#SamplePointUID', data.items, clear=true, add_empty=true)
      
      command = 'search?portal_type=SampleType'
      result = me.api.get_json command, method: "GET"
      result.then (data) ->
         console.log('Items returned: ' + data.items.length)
         me.populate_dropdown('#SampleTypeUID', data.items, clear=false, add_empty=false)

         command = 'search?portal_type=AnalysisSpec'
         result = me.api.get_json command, method: "GET"
         result.then (data) ->
            console.log('Items returned: ' + data.items.length)
            me.populate_dropdown('#spec', data.items, clear=true, add_empty=true)

            command = 'search?portal_type=AnalysisService'
            result = me.api.get_json command, method: "GET"
            result.then (data) ->
               console.log('Items returned: ' + data.items.length)
               me.populate_dropdown('#ServiceUID', data.items, clear=true, add_empty=true)

               command = 'search?portal_type=AnalysisService'
               result = me.api.get_json command, method: "GET"
               result.then (data) ->
                  console.log('Items returned: ' + data.items.length)
                  me.populate_dropdown('#SecondServiceUID', data.items, clear=true, add_empty=true)

  sample_point_selected: (selected_sample_point) =>
    console.log 'Got SamplePointUID" ' + selected_sample_point
    me = this
    if selected_sample_point
      command = 'samplepoint/' + selected_sample_point
   
      # Get samplepoint
      result = me.api.get_json command, method: "GET"
      result.then (data) ->
         console.log('Items returned: ' + data.items.length)
         command = 'search?portal_type=SampleType'
         sample_type_uids = me.get_object_values('sample_types', data.items)
         if sample_type_uids
           for sample_type_uid in sample_type_uids
             command += '&UID=' + sample_type_uid
       
         # Get items
         result = me.api.get_json command, method: "GET"
         result.then (data) ->
            console.log('Items returned: ' + data.items.length)
            me.populate_dropdown('#SampleTypeUID', data.items, clear=true, add_empty=true)

            command = 'search?portal_type=AnalysisSpec'
            result = me.api.get_json command, method: "GET"
            result.then (data) ->
               console.log('Items returned: ' + data.items.length)
               me.populate_dropdown('#spec', data.items, clear=true, add_empty=true)

               command = 'search?portal_type=AnalysisService'
               result = me.api.get_json command, method: "GET"
               result.then (data) ->
                  console.log('Items returned: ' + data.items.length)
                  me.populate_dropdown('#ServiceUID', data.items, clear=true, add_empty=true)

                  command = 'search?portal_type=AnalysisService'
                  result = me.api.get_json command, method: "GET"
                  result.then (data) ->
                     console.log('Items returned: ' + data.items.length)
                     me.populate_dropdown('#SecondServiceUID', data.items, clear=true, add_empty=true)


  sample_type_selected: (selected_sample_type) =>
    console.log 'Got SampleTypeUID" ' + selected_sample_type
    me = this
    if selected_sample_type
       command = 'search?portal_type=AnalysisSpec&sampletype_uid=' + selected_sample_type
     
       # Get items
       result = me.api.get_json command, method: "GET"
       result.then (data) ->
          console.log('Items returned: ' + data.items.length)
          me.populate_dropdown('#spec', data.items, clear=true, add_empty=true)

          command = 'search?portal_type=AnalysisService'
          result = me.api.get_json command, method: "GET"
          result.then (data) ->
             console.log('Items returned: ' + data.items.length)
             me.populate_dropdown('#ServiceUID', data.items, clear=true, add_empty=true)

             command = 'search?portal_type=AnalysisService'
             result = me.api.get_json command, method: "GET"
             result.then (data) ->
                console.log('Items returned: ' + data.items.length)
                me.populate_dropdown('#SecondServiceUID', data.items, clear=true, add_empty=true)

  analysis_spec_selected: (selected_analysis_spec) =>
    console.log 'Got AnalysisSpec" ' + selected_analysis_spec
    me = this
    if selected_analysis_spec
      command = 'analysisspec/' + selected_analysis_spec
      result = me.api.get_json command, method: "GET"
      result.then (data) ->
         service_uids = me.get_object_values('ResultsRange', data.items)

         command = 'search?portal_type=AnalysisService'
         if service_uids
           for service_uid in service_uids
             command += '&UID=' + service_uid
   
           # Get Services
           result = me.api.get_json command, method: "GET"
           result.then (data) ->
              console.log('Items returned: ' + data.items.length)
              me.populate_dropdown('#ServiceUID', data.items, clear=true, add_empty=true)
              # me.populate_dropdown('#SecondServiceUID', data.items, clear=true, add_empty=true)


  on_dropdown_change: (e) =>
    ###*
     * Event handler when dropdown changed
    ###
    $el = $(e.currentTarget)
    console.log "°°° ReportFolderView::on_dropdown_change on " + $el.id + " °°°"
    outer_parent = $el.closest('.update_dropdown')
    if not $el.closest('.update_dropdown').length
      return

    console.log 'update_dropdown: ' + e.target.id
    e.preventDefault()

    if e.target.id == 'ClientUID'
      console.log 'ClientUID selected'
      selected_client = $(e.target).val()
      @client_selected selected_client

    if e.target.id == 'SamplePointUID'
      console.log 'SamplePointUID selected'
      selected_sample_point = $(e.target).val()
      @sample_point_selected selected_sample_point

    if e.target.id == 'SampleTypeUID'
      console.log 'SampleTypeUID selected'
      selected_sample_type = $(e.target).val()
      @sample_type_selected selected_sample_type

    if e.target.id == 'spec'
      console.log 'spec selected'
      selected_analysis_spec = $(e.target).val()
      @analysis_spec_selected selected_analysis_spec

    console.log 'on_dropdown_change complete'



obj = new window["ReportFolderView"]()
obj.load()
