(function() {
  /*
   * Publish API Module
   */
  var ReportsAPI;

  /* Please use this command to compile this file into the parent `js` directory:
      coffee --no-header -w -o ../ -c api.coffee
  */
  ReportsAPI = class ReportsAPI {
    constructor() {
      console.debug("ReportsAPI::constructor");
      return this;
    }

    parse_html(html) {
      /*
       * Parse the HTML to a DOM element
       */
      var parser;
      parser = new DOMParser();
      return parser.parseFromString(html, "text/html");
    }

    get_base_url() {
      /*
       * Calculate the current base url
       */
      return document.URL.split("?")[0];
    }

    get_api_url(endpoint) {
      var aa, api_endpoint, api_url, current_view, params, segments, url;
      /*
       * Build API URL for the given endpoint
       * @param {string} endpoint
       * @returns {string}
       */
      // api_endpoint = "ajax_publish"
      aa = "http://localhost:8080/lims/@@API/senaite/v1/client";
      api_endpoint = "@@API/senaite/v1";
      segments = location.pathname.split("/");
      current_view = segments[segments.length - 1];
      url = this.get_base_url().split(current_view)[0];
      // we also pass back eventual query parameters to the API
      params = location.search;
      api_url = `${url}${api_endpoint}/${endpoint}${params}`;
      console.info(`ReportsAPI::get_api_url=${api_url}`);
      return api_url;
    }

    get_url_parameter(name) {
      var regex, results;
      name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
      regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
      results = regex.exec(location.search);
      if (results === null) {
        return '';
      } else {
        return decodeURIComponent(results[1].replace(/\+/g, ' '));
      }
    }

    get_items() {
      /*
       * Parse the `items` request parameter and returns the UIDs in an array
       */
      var items;
      items = this.get_url_parameter("items");
      return items.split(",");
    }

    get_reports(uids) {
      var options;
      /*
       * Fetch the JSON data of all the reports
       */
      if (!uids) {
        uids = this.get_items();
      }
      options = {
        data: {
          items: uids
        }
      };
      return this.get_json("get_reports", options);
    }

    get_json(endpoint, options) {
      var data, init, method, request, url;
      /*
       * Fetch Ajax API resource from the server
       * @param {string} endpoint
       * @param {object} options
       * @returns {Promise}
       */
      if (options == null) {
        options = {};
      }
      method = options.method || "POST";
      data = JSON.stringify(options.data) || "{}";
      url = this.get_api_url(endpoint);
      init = {
        method: method,
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-TOKEN": this.get_csrf_token()
        },
        body: method === "POST" ? data : null,
        credentials: "include"
      };
      console.info(`ReportsAPI::fetch:endpoint=${endpoint} init=`, init);
      request = new Request(url, init);
      console.info(`ReportsAPI::fetch:url=${url} request=`, request);
      return fetch(request).then(function(response) {
        if (response.status !== 200) {
          return response.json().then(function(json) {
            throw new Error(json.error || "Unknown Error");
          });
        } else {
          return response.json();
        }
      });
    }

    render_reports(data) {
      /*
       * Fetch the generated reports HTML from the server
       * @returns {Promise}
       */
      var options;
      options = {
        data: data
      };
      return this.get_json("render_reports", options);
    }

    save_reports(data) {
      /*
       * @returns {Promise}
       */
      var options;
      options = {
        data: data
      };
      return this.get_json("save_reports", options);
    }

    create_pdf(options) {
      var formData, init, key, request, url, value;
      // wrap all options into form data
      formData = new FormData();
      formData.set("download", "1");
      for (key in options) {
        value = options[key];
        formData.set(key, value);
      }
      // Prepare the POST request
      url = this.get_base_url();
      init = {
        method: "POST",
        body: formData,
        credentials: "include"
      };
      request = new Request(url, init);
      // submit the POST and display the PDF in a new window
      return fetch(request).then(function(response) {
        return response.blob();
      });
    }

    print_pdf(options) {
      /*
       * Send an async request to the server and download the file
       */
      return this.create_pdf(options).then(function(blob) {
        var url;
        // open the PDF in a separate window
        url = window.URL.createObjectURL(blob);
        return window.open(url, "_blank");
      });
    }

    // Alternate way to download a named PDF

    // window.URL.revokeObjectURL(url)
    // use this for immediate download
    // fileLink = document.createElement("a")
    // fileLink.href = url
    // fileLink.download = options.filename or "Report.pdf"
    // fileLink.click()
    load_preview(data) {
      /*
       * Fetch the generated previews HTML (including PNGs) from the server
       * @returns {Promise}
       */
      var options;
      options = {
        data: data
      };
      return this.get_json("load_preview", options);
    }

    fetch_templates() {
      /*
       * Fetch available templates
       * @returns {Promise}
       */
      return this.get_json("templates", {
        method: "GET"
      });
    }

    fetch_config() {
      /*
       * Fetch default config
       * @returns {Promise}
       */
      return this.get_json("config", {
        method: "GET"
      });
    }

    fetch_paperformats() {
      /*
       * Fetch paperformats from the server
       * @returns {Promise}
       */
      return this.get_json("paperformats", {
        method: "GET"
      });
    }

    render_barcodes() {
      /*
       * Render Barcodes
       */
      return $('.barcode').each(function() {
        var addQuietZone, barHeight, barcode_hri, code, id, showHRI;
        id = $(this).attr('data-id');
        console.debug(`Render Barcode ${id}`);
        code = $(this).attr('data-code');
        barHeight = $(this).attr('data-barHeight');
        addQuietZone = $(this).attr('data-addQuietZone');
        showHRI = $(this).attr('data-showHRI');
        $(this).barcode(id, code, {
          'barHeight': parseInt(barHeight),
          'addQuietZone': addQuietZone === 'true',
          'showHRI': showHRI === 'true',
          'output': 'bmp'
        });
        if (showHRI === 'true') {
          // When output is set to "bmp", the showHRI parameter (that
          // prints the ID below the barcode) is dissmissed by barcode.js
          // so we need to add it manually
          $(this).find('.barcode-hri').remove();
          barcode_hri = '<div class=\'barcode-hri\'>' + id + '</div>';
          return $(this).append(barcode_hri);
        }
      });
    }

    render_qrcodes() {
      /*
       * Render QR codes
       */
      return $('.qrcode').each(function() {
        var color, size, text;
        text = $(this).attr('data-text');
        console.debug(`Render QR Code ${text}`);
        size = $(this).attr('data-size');
        color = $(this).attr('data-color');
        $(this).qrcode({
          'size': size,
          'color': color,
          'text': text,
          'render': 'image'
        });
        // Render this QR only once
        return $(this).removeClass("qrcode");
      });
    }

    render_ranges() {
      /*
       * Render ranges (graphs)
       */
      new RangeGraph().load();
      return this.convert_svg_to_image();
    }

    convert_svg_to_image() {
      /*
       * Convert SVGs to Images
       */
      return jQuery("svg").each(function() {
        var img;
        console.debug("Convert SVG to IMG: ", this);
        img = document.createElement("img");
        img.src = "data:image/svg+xml;base64," + btoa($(this).parent().html());
        return jQuery(this).replaceWith(img);
      });
    }

    get_csrf_token() {
      /*
       * Get the plone.protect CSRF token
       * Note: The fields won't save w/o that token set
       */
      return document.querySelector("#protect-script").dataset.token;
    }

  };

  // Export for use in other modules
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = ReportsAPI;
  } else if (typeof window !== 'undefined') {
    window.ReportsAPI = ReportsAPI;
  }

}).call(this);
