(function() {
  /* Please use this command to compile this file into the parent `js` directory:
      coffee --no-header -w -o ../ -c bika.lims.reports.coffee
  */
  var obj;

  window.ReportFolderView = class ReportFolderView {
    constructor() {
      this.load = this.load.bind(this);
      /* INITIALIZERS */
      this.bind_eventhandler = this.bind_eventhandler.bind(this);
      this.on_toggle_change = this.on_toggle_change.bind(this);
      this.call_command = this.call_command.bind(this);
      this.populate_dropdown = this.populate_dropdown.bind(this);
      this.get_object_values = this.get_object_values.bind(this);
      this.client_selected = this.client_selected.bind(this);
      this.sample_point_selected = this.sample_point_selected.bind(this);
      this.sample_type_selected = this.sample_type_selected.bind(this);
      this.analysis_spec_selected = this.analysis_spec_selected.bind(this);
      this.on_dropdown_change = this.on_dropdown_change.bind(this);
    }

    load() {
      console.debug("ReportFolderView::load");
      // initialize toggle anchors
      this.bind_eventhandler();
      // initialize api
      return this.api = new ReportsAPI();
    }

    bind_eventhandler() {
      /*
       * Binds callbacks on elements
       */
      console.debug("ReportFolderView::bind_eventhandler");
      // When the anchor for a given report is selected, display the report form
      $("body").on("click", "a[id$='_selector']", this.on_toggle_change);
      // When the dropdown is changed for a given select, update dependant dropdown
      return $("body").on("change", "select", this.on_dropdown_change);
    }

    on_toggle_change(event) {
      var div_id;
      /**
       * Event handler when the toggle anchor is clicked
       */
      console.debug("°°° ReportFolderView::on_toggle_change °°°");
      event.preventDefault();
      $(".criteria").toggle(false);
      div_id = event.currentTarget.id.split("_selector")[0];
      return $("[id='" + div_id + "']").toggle(true);
    }

    call_command(command, limit = 1000) {
      var result;
      if (limit) {
        command += '&limit=' + limit;
      }
      console.log("call_command: " + command);
      result = this.api.get_json(command, {
        method: "GET"
      });
      return result;
    }

    populate_dropdown(el_name, items, clear = true, add_empty = false) {
      var $el, i, item, len, results, sorted_items;
      // Empty select
      $el = $(el_name);
      
      // Empty select if specified
      if (clear) {
        $el.empty();
      }
      // Add new options
      if (add_empty) {
        $('<option>').val('').text('').appendTo($el); // Empty option
      }
      
      // sort items
      sorted_items = items.sort(function(a, b) {
        if (a.title < b.title) {
          return -1;
        } else if (a.title > b.title) {
          return 1;
        } else {
          return 0;
        }
      });
// Add new options
      results = [];
      for (i = 0, len = sorted_items.length; i < len; i++) {
        item = sorted_items[i];
        results.push($('<option>').val(item.uid).text(item.title).appendTo($el));
      }
      return results;
    }

    get_object_values(fieldname, items) {
      var i, item, j, len, len1, ref, result, val;
      result = [];
      for (i = 0, len = items.length; i < len; i++) {
        item = items[i];
        if (item.hasOwnProperty(fieldname)) {
          ref = item[fieldname];
          for (j = 0, len1 = ref.length; j < len1; j++) {
            val = ref[j];
            result.push(val['uid']);
          }
        }
      }
      return result;
    }

    client_selected(selected_client) {
      var command, me, result;
      console.log('Got ClientUID: ' + selected_client);
      me = this;
      if (selected_client) {
        command = 'search?portal_type=SamplePoint&getClientUID=&getClientUID=' + selected_client;
      } else {
        command = 'search?portal_type=SamplePoint&getClientUID=';
      }
      // Get items
      result = me.call_command(command);
      return result.then(function(data) {
        var add_empty, clear;
        console.log('Items returned: ' + data.items.length);
        me.populate_dropdown('#SamplePointUID', data.items, clear = true, add_empty = true);
        command = 'search?portal_type=SampleType';
        result = me.call_command(command);
        return result.then(function(data) {
          console.log('Items returned: ' + data.items.length);
          me.populate_dropdown('#SampleTypeUID', data.items, clear = true, add_empty = true);
          command = 'search?portal_type=AnalysisSpec';
          result = me.call_command(command);
          return result.then(function(data) {
            console.log('Items returned: ' + data.items.length);
            me.populate_dropdown('#analysis_spec', data.items, clear = true, add_empty = true);
            command = 'search?portal_type=AnalysisService';
            result = me.call_command(command);
            return result.then(function(data) {
              console.log('Items returned: ' + data.items.length);
              me.populate_dropdown('#ServiceUID', data.items, clear = true, add_empty = false);
              return me.populate_dropdown('#SecondServiceUID', data.items, clear = true, add_empty = true);
            });
          });
        });
      });
    }

    sample_point_selected(selected_sample_point) {
      var command, limit, me, result;
      console.log('Got SamplePointUID" ' + selected_sample_point);
      me = this;
      if (selected_sample_point) {
        command = 'samplepoint/' + selected_sample_point;
        
        // Get samplepoint
        result = me.call_command(command, limit = 0);
        return result.then(function(data) {
          var i, len, sample_type_uid, sample_type_uids;
          console.log('Items returned: ' + data.items.length);
          command = 'search?portal_type=SampleType';
          sample_type_uids = me.get_object_values('sample_types', data.items);
          if (sample_type_uids) {
            for (i = 0, len = sample_type_uids.length; i < len; i++) {
              sample_type_uid = sample_type_uids[i];
              command += '&UID=' + sample_type_uid;
            }
          }
          
          // Get items
          result = me.call_command(command);
          return result.then(function(data) {
            var add_empty, clear;
            console.log('Items returned: ' + data.items.length);
            me.populate_dropdown('#SampleTypeUID', data.items, clear = true, add_empty = true);
            command = 'search?portal_type=AnalysisSpec';
            result = me.call_command(command);
            return result.then(function(data) {
              console.log('Items returned: ' + data.items.length);
              me.populate_dropdown('#analysis_spec', data.items, clear = true, add_empty = true);
              command = 'search?portal_type=AnalysisService';
              result = me.call_command(command);
              return result.then(function(data) {
                console.log('Items returned: ' + data.items.length);
                me.populate_dropdown('#ServiceUID', data.items, clear = true, add_empty = false);
                return me.populate_dropdown('#SecondServiceUID', data.items, clear = true, add_empty = true);
              });
            });
          });
        });
      }
    }

    sample_type_selected(selected_sample_type) {
      var command, me, result;
      console.log('Got SampleTypeUID" ' + selected_sample_type);
      me = this;
      if (selected_sample_type) {
        command = 'search?portal_type=AnalysisSpec&sampletype_uid=' + selected_sample_type;
      } else {
        command = 'search?portal_type=AnalysisSpec';
      }
      
      // Get items
      result = me.call_command(command);
      return result.then(function(data) {
        var add_empty, clear;
        console.log('Items returned: ' + data.items.length);
        me.populate_dropdown('#analysis_spec', data.items, clear = true, add_empty = true);
        command = 'search?portal_type=AnalysisService';
        result = me.call_command(command);
        return result.then(function(data) {
          console.log('Items returned: ' + data.items.length);
          me.populate_dropdown('#ServiceUID', data.items, clear = true, add_empty = false);
          return me.populate_dropdown('#SecondServiceUID', data.items, clear = true, add_empty = true);
        });
      });
    }

    analysis_spec_selected(selected_analysis_spec) {
      var command, limit, me, result;
      console.log('Got AnalysisSpec" ' + selected_analysis_spec);
      me = this;
      if (selected_analysis_spec) {
        command = 'analysisspec/' + selected_analysis_spec;
        result = me.call_command(command, limit = 0);
        return result.then(function(data) {
          var i, len, service_uid, service_uids;
          service_uids = me.get_object_values('ResultsRange', data.items);
          command = 'search?portal_type=AnalysisService';
          if (service_uids) {
            for (i = 0, len = service_uids.length; i < len; i++) {
              service_uid = service_uids[i];
              command += '&UID=' + service_uid;
            }
            
            // Get Services
            result = me.call_command(command);
            return result.then(function(data) {
              var add_empty, clear;
              console.log('Items returned: ' + data.items.length);
              me.populate_dropdown('#ServiceUID', data.items, clear = true, add_empty = false);
              return me.populate_dropdown('#SecondServiceUID', data.items, clear = true, add_empty = true);
            });
          }
        });
      } else {
        // Get Services
        command = 'search?portal_type=AnalysisService';
        result = me.call_command(command);
        return result.then(function(data) {
          var add_empty, clear;
          console.log('Items returned: ' + data.items.length);
          me.populate_dropdown('#ServiceUID', data.items, clear = true, add_empty = false);
          return me.populate_dropdown('#SecondServiceUID', data.items, clear = true, add_empty = true);
        });
      }
    }

    on_dropdown_change(e) {
      /**
       * Event handler when dropdown changed
       */
      var $el, outer_parent, selected_analysis_spec, selected_client, selected_sample_point, selected_sample_type;
      $el = $(e.currentTarget);
      console.log("°°° ReportFolderView::on_dropdown_change on " + $el.id + " °°°");
      outer_parent = $el.closest('.update_dropdown');
      if (!$el.closest('.update_dropdown').length) {
        return;
      }
      console.log('update_dropdown: ' + e.target.id);
      e.preventDefault();
      if (e.target.id === 'ClientUID') {
        console.log('ClientUID selected');
        selected_client = $(e.target).val();
        this.client_selected(selected_client);
      }
      if (e.target.id === 'SamplePointUID') {
        selected_sample_point = $(e.target).val();
        console.log('SamplePointUID selected: ' + selected_sample_point);
        this.sample_point_selected(selected_sample_point);
      }
      if (e.target.id === 'SampleTypeUID') {
        console.log('SampleTypeUID selected');
        selected_sample_type = $(e.target).val();
        this.sample_type_selected(selected_sample_type);
      }
      if (e.target.id === 'analysis_spec') {
        console.log('analysis_spec selected');
        selected_analysis_spec = $(e.target).val();
        this.analysis_spec_selected(selected_analysis_spec);
      }
      return console.log('on_dropdown_change complete');
    }

  };

  obj = new window["ReportFolderView"]();

  obj.load();

}).call(this);
