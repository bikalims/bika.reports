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
    }

    load() {
      console.debug("ReportFolderView::load");
      // initialize toggle anchors
      return this.bind_eventhandler();
    }

    bind_eventhandler() {
      /*
       * Binds callbacks on elements
       */
      console.debug("ReportFolderView::bind_eventhandler");
      // When the anchor for a given report is selected, display the report form
      return $("body").on("click", "a[id$='_selector']", this.on_toggle_change);
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

  };

  obj = new window["ReportFolderView"]();

  obj.load();

}).call(this);
