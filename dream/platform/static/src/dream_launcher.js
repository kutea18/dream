/* ===========================================================================
 * Copyright 2013 Nexedi SA and Contributors
 *
 * This file is part of DREAM.
 *
 * DREAM is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * DREAM is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with DREAM.  If not, see <http://www.gnu.org/licenses/>.
 * =========================================================================== */

(function ($) {
  "use strict";
  jsPlumb.bind("ready", function () {
    var dream_instance, jio;
    jio = new jIO.newJio({
      type: "local",
      username: "dream",
      applicationname: "dream"
    });

    var configuration = { };

    $.ajax(
        '../getConfigurationDict', {
       success: function (data) {
         configuration = $.extend(configuration, data);

    dream_instance = Dream(configuration);
    dream_instance.start();

    $(".tool").draggable({
      containment: '#main',
      opacity: 0.7,
      helper: "clone",
      cursorAt: {
        top: 0,
        left: 0
      },
      stop: function (tool) {
        var box_top, box_left, _class;
        var offset = $("#main").offset();
        box_top = tool.clientY - offset.top + "px";
        box_left = tool.clientX - offset.left + "px";
        var relative_position = dream_instance.convertToRelativePosition(
          box_left, box_top);
        _class = tool.target.id.replace('-', '.'); // XXX - vs .
        dream_instance.newElement({
          coordinate: {
            top: relative_position[1],
            left: relative_position[0]
          },
          _class: _class
        });
      }
    });

    var loadData = function (data) {
      dream_instance.clearAll();
      $('#reports').hide();
      $('#result_zone').hide();

      $('#shift_spreadsheet').hide();
      $("#debug_json").hide();
      $("#wip_part_spreadsheet").hide();

      if (configuration['Dream-Configuration'].gui.wip_part_spreadsheet){
        $("#wip_part_spreadsheet").show();
      }
      if (configuration['Dream-Configuration'].gui.shift_spreadsheet){
        $("#shift_spreadsheet").show();
      }
      if (configuration['Dream-Configuration'].gui.debug_json){
        $("#debug_json").show();
      }

      try {
        // spreadsheets
        var shift_spreadsheet_data = data.shift_spreadsheet;
        if (shift_spreadsheet_data !== undefined) {
          var spreadsheet = $('#shift_spreadsheet');
          spreadsheet.handsontable('populateFromArray', 0, 0, shift_spreadsheet_data);
        }
        var wip_part_spreadsheet_data = data.wip_part_spreadsheet;
        if (wip_part_spreadsheet_data !== undefined) {
          var spreadsheet = $('#wip_part_spreadsheet');
          spreadsheet.handsontable('populateFromArray', 0, 0, wip_part_spreadsheet_data);
        }

        var preference = data.preference !== undefined ?
          data.preference : {};
        dream_instance.setPreferences(preference);

        // Add all elements
        var coordinates = preference['coordinates'];
        $.each(data.nodes, function (key, value) {
          if (coordinates === undefined || coordinates[key] === undefined) {
            value['coordinate'] = {
              'top': 0.0,
              'left': 0.0
            };
          } else {
            value['coordinate'] = coordinates[key];
          }
          value['id'] = key;
          dream_instance.newElement(value);
          if (value.data) { // backward compatibility
            dream_instance.updateElementData(key, {
              data: value.data
            });
          }
        });
        $.each(data.edges, function (key, value) {
          dream_instance.connect(value[0], value[1]);
        });

        dream_instance.updateGeneralProperties(data.general);
        dream_instance.prepareDialogForGeneralProperties();
        $("#json_output").val(JSON.stringify(dream_instance.getData(),
          undefined, " "));
        if ($.isEmptyObject(coordinates)) {
          dream_instance.positionGraph();
        } else {
          dream_instance.redraw();
        }
      } catch (e) {
        alert('Loading data failed.');
        console.error(e);
      }
    };
    // Check if there is already data when we first load the page, if yes, then build graph from it
    jio.get({
      _id: "dream_demo"
    }, function (err, response) {
      if (response !== undefined && response.data !== undefined) {
        loadData(response.data);
      }
      // once the data is read, we can subscribe to every changes
      $.subscribe("Dream.Gui.onDataChange", function (event, data) {
        $("#json_output").val(JSON.stringify(data, undefined, " "));
        jio.put({
          _id: "dream_demo",
          data: data
        }, function (err, response) {});
      });
    });


    // Enable "Run Simulation" button
    $("#run_simulation").button().click(
      function (e) {
        $("#loading_spinner").show();
        $("#run_simulation").button('disable');
        dream_instance.runSimulation(
          function (data) {
            $("#loading_spinner").hide();
            $("#run_simulation").button('enable');
            $("#reports").show();
            $("#result_zone").show();
            $('#result_list').empty();
            if (data['success']) {
              $("#json_result").val(JSON.stringify(data['success'],
                undefined, " "));
              $.each(data['success'], function (idx, obj) {
                $('#result_list').append('<li class="result"></li>');
                $('#result_list').children().last().text(idx + ' : ' + obj['score'] + ' ' + obj['key']).click(
                  function (e) {
                    dream_instance.displayResult(idx);
                  }
                );
              });
              dream_instance.displayResult(0);
            } else {
              $("#reports").hide();
              $("#json_result").show().effect('shake', 50).val(data['error']);
              console.error(data['error'])
            }
          });
        e.preventDefault();
        return false;
      });

    // Enable "Layout Graph" button
    $("#layout_graph").button().click(
      function (e) {
        dream_instance.positionGraph();
      });

    // Enable "Clear All" button
    $("#clear_all").button().click(
      function (e) {
        if (confirm("Are you sure you want to clear all ?")) {
          dream_instance.clearAll();
          e.preventDefault();
        }
        return false;
      });

    // Enable "Zoom +" button
    $("#zoom_in").button().click(
      function (e) {
        dream_instance.zoom_in();
      });

    // Enable "Zoom -" button
    $("#zoom_out").button().click(
      function (e) {
        dream_instance.zoom_out();
      });

    // Enable "Export" button
    $("#export").button().click(
      function (e) {
        $('#export_json').val(JSON.stringify(dream_instance.getData()));
        $('#export_form').submit();
        return false;
      });

    // Enable "Import" button
    $("#import").button().click(
      function (e) {
        $('#import_file').click();
      });
    $("#import_file").change(function () {
      var form = $(this).parent('form')[0];
      var form_data = new FormData(form);
      $.ajax('../postJSONFile', {
        type: 'POST',
        contentType: false,
        processData: false,
        data: form_data,
        dataType: 'json',
        error: function () {
          console.error('error');
        },
        success: function (data, textStatus, jqXHR) {
          form.reset();
          $("#json_output").val(JSON.stringify(data));
          loadData(data);
        }
      });
      return false;
    });

    // Redraw if the graph area or the window is resized
    $('#main').resizable().resize(function () {
      dream_instance.redraw();
    });
    $(window).resize(function () {
      dream_instance.redraw();
    });
    $("#job_schedule_spreadsheet").hide();
    $("#shift_spreadsheet").hide();
       }
    });
  });
})(jQuery);
