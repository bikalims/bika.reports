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
      this.initialize_plugins = this.initialize_plugins.bind(this);
      this.on_toggle_change = this.on_toggle_change.bind(this);
      this.call_command = this.call_command.bind(this);
      this.populate_dropdown = this.populate_dropdown.bind(this);
      // # Empty select
      // $el = $(el_name)

      // # Empty select if specified
      // if clear
      //   $el.empty()

      // # Add new options
      // if add_empty
      //   $('<option>').val('').text('').appendTo($el)  # Empty option

      // # Add new options
      // for item in sorted_items
      //   $('<option>').val(item.uid).text(item.title).appendTo($el)
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
      this.api = new ReportsAPI();
      // Use requestAnimationFrame to wait for DOM painting
      return requestAnimationFrame(() => {
        return this.initialize_plugins();
      });
    }

    bind_eventhandler() {
      /*
       * Binds callbacks on elements
       */
      console.debug("ReportFolderView::bind_eventhandler");
      // When the anchor for a given report is selected, display the report form
      return $("body").on("click", "a[id$='_selector']", this.on_toggle_change);
    }

    initialize_plugins() {
      console.log("TomSelect is a " + typeof TomSelect);
      if (typeof TomSelect === "undefined") {
        console.warn("TomSelect not ready, retrying...");
        setTimeout(this.initialize_plugins, 50);
        return;
      }
      this.tomselects = {};
      $(".tomsel").each((i, el) => {
        var err, select_el, ts;
        select_el = el.childNodes[0].childNodes[3];
        try {
          ts = new TomSelect(select_el, {
            create: false,
            allowEmptyOption: true,
            placeholder: "Choose an option",
            sortField: {
              field: "text",
              direction: "asc"
            }
          });
          this.tomselects[select_el.id] = ts;
          console.debug("Wrapper: " + ts.wrapper);
          console.debug("Input: " + ts.input);
          return console.debug("TomSelect init worked " + select_el);
        } catch (error) {
          err = error;
          return console.error("TomSelect init failed:", err);
        }
      });
      // When the dropdown is changed for a given select, update dependant dropdown
      // $("#ClientUID").on "change", "select", @on_dropdown_change
      $("body").on("change", "select", this.on_dropdown_change);
      return console.log("TomSelect initialised");
    }

    on_toggle_change(event) {
      var div_id;
      /**
       * Event handler when the toggle anchor is clicked
       */
      console.debug("°°° ReportFolderView::on_toggle_change with" + event + " °°°");
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
      var data, item, j, k, len, len1, opt, ts;
      console.log("populate_dropdown: " + el_name);
      // eransform to [{value: "foo", text: "Foo"}, ...]
      data = [];
      for (j = 0, len = items.length; j < len; j++) {
        item = items[j];
        data.push({
          value: item['uid'],
          text: item['title']
        });
      }
      // Assume data.options is [{value: "foo", text: "Foo"}, ...]
      ts = this.tomselects[el_name];
      if (ts != null) {
        ts.clearOptions();
        for (k = 0, len1 = data.length; k < len1; k++) {
          opt = data[k];
          ts.addOption(opt);
        }
        return ts.refreshOptions(false);
      } else {
        return console.error('populate_dropdown: missing TS element ' + el_name + ' in ' + this.tomselects);
      }
    }

    get_object_values(fieldname, items) {
      var item, j, k, len, len1, ref, result, val;
      result = [];
      for (j = 0, len = items.length; j < len; j++) {
        item = items[j];
        if (item.hasOwnProperty(fieldname)) {
          ref = item[fieldname];
          for (k = 0, len1 = ref.length; k < len1; k++) {
            val = ref[k];
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
        console.debug('Items returned: ' + data.items.length);
        me.populate_dropdown('SamplePointUID', data.items, clear = true, add_empty = true);
        command = 'search?portal_type=SampleType';
        result = me.call_command(command);
        return result.then(function(data) {
          console.debug('Items returned: ' + data.items.length);
          me.populate_dropdown('SampleTypeUID', data.items, clear = true, add_empty = true);
          command = 'search?portal_type=AnalysisSpec';
          result = me.call_command(command);
          return result.then(function(data) {
            console.debug('Items returned: ' + data.items.length);
            me.populate_dropdown('analysis_spec', data.items, clear = true, add_empty = true);
            command = 'search?portal_type=AnalysisService';
            result = me.call_command(command);
            return result.then(function(data) {
              console.debug('Items returned: ' + data.items.length);
              me.populate_dropdown('ServiceUID', data.items, clear = true, add_empty = false);
              return me.populate_dropdown('SecondServiceUID', data.items, clear = true, add_empty = true);
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
          var j, len, sample_type_uid, sample_type_uids;
          console.debug('Items returned: ' + data.items.length);
          command = 'search?portal_type=SampleType';
          sample_type_uids = me.get_object_values('sample_types', data.items);
          if (sample_type_uids) {
            for (j = 0, len = sample_type_uids.length; j < len; j++) {
              sample_type_uid = sample_type_uids[j];
              command += '&UID=' + sample_type_uid;
            }
          }
          
          // Get items
          result = me.call_command(command);
          return result.then(function(data) {
            var add_empty, clear;
            console.debug('Items returned: ' + data.items.length);
            me.populate_dropdown('SampleTypeUID', data.items, clear = true, add_empty = true);
            command = 'search?portal_type=AnalysisSpec';
            result = me.call_command(command);
            return result.then(function(data) {
              console.debug('Items returned: ' + data.items.length);
              me.populate_dropdown('analysis_spec', data.items, clear = true, add_empty = true);
              command = 'search?portal_type=AnalysisService';
              result = me.call_command(command);
              return result.then(function(data) {
                console.debug('Items returned: ' + data.items.length);
                me.populate_dropdown('ServiceUID', data.items, clear = true, add_empty = false);
                return me.populate_dropdown('SecondServiceUID', data.items, clear = true, add_empty = true);
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
        console.debug('Items returned: ' + data.items.length);
        me.populate_dropdown('analysis_spec', data.items, clear = true, add_empty = true);
        command = 'search?portal_type=AnalysisService';
        result = me.call_command(command);
        return result.then(function(data) {
          console.debug('Items returned: ' + data.items.length);
          me.populate_dropdown('ServiceUID', data.items, clear = true, add_empty = false);
          return me.populate_dropdown('SecondServiceUID', data.items, clear = true, add_empty = true);
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
          var j, len, service_uid, service_uids;
          service_uids = me.get_object_values('ResultsRange', data.items);
          command = 'search?portal_type=AnalysisService';
          if (service_uids) {
            for (j = 0, len = service_uids.length; j < len; j++) {
              service_uid = service_uids[j];
              command += '&UID=' + service_uid;
            }
            
            // Get Services
            result = me.call_command(command);
            return result.then(function(data) {
              var add_empty, clear;
              console.debug('Items returned: ' + data.items.length);
              me.populate_dropdown('ServiceUID', data.items, clear = true, add_empty = false);
              return me.populate_dropdown('SecondServiceUID', data.items, clear = true, add_empty = true);
            });
          }
        });
      } else {
        // Get Services
        command = 'search?portal_type=AnalysisService';
        result = me.call_command(command);
        return result.then(function(data) {
          var add_empty, clear;
          console.debug('Items returned: ' + data.items.length);
          me.populate_dropdown('ServiceUID', data.items, clear = true, add_empty = false);
          return me.populate_dropdown('SecondServiceUID', data.items, clear = true, add_empty = true);
        });
      }
    }

    on_dropdown_change(e) {
      var $el, outer_parent, selected_analysis_spec, selected_client, selected_sample_point, selected_sample_type;
      /**
       * Event handler when dropdown changed
       */
      console.debug("°°° ReportFolderView::on_dropdown_change on e " + e.id + " °°°");
      if (e.currentTarget) {
        $el = $(e.currentTarget);
      } else {
        $el = $(e);
      }
      console.log("°°° ReportFolderView::on_dropdown_change on target" + $el.id + " °°°");
      outer_parent = $el.closest('.update_dropdown');
      if (!$el.closest('.update_dropdown').length) {
        console.log('element ' + $el + ' not closest to update_dropdown');
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
