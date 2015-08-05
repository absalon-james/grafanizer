/* global _ */

/*
 * Complex scripted dashboard
 * This script generates a dashboard with a single text panel. The text panel
 * contains a list of links to dashboards saved in the elastic search backend.
 *
 * Global accessable variables
 * window, document, $, jQuery, ARGS, moment
 *
 * Return a dashboard object, or a function
 *
 * For async scripts, return a function, this function must take a single
 * callback function, call this function with the dasboard object
 */

// Make clicking on a row follow the link contained in the row.
$(document).on('click', '.default-list-item', function(event) {
    event.preventDefault();
    window.location = $(this).find("a").attr('href');
});

function create_row($content) {
    return {
        height: '300px',
        panels: [{
            title: ' ',
            type: 'text',
            span: 12,
            fill: 0,
            mode: 'html',
            content: $content.html()
        }]
    };
}

function dashboard_uri(hit) {
    return encodeURI('/#/dashboard/db/' + hit._id);
}

function dashboard_row(hit) {
    var href = dashboard_uri(hit);
    var $row = $('<div></div>');
    $row.addClass('search-result-item default-list-item pointer');
    $anchor =  $('<a></a>').addClass('search-result-link').attr('href', href);
    $('<i class="icon icon-th-large"></i>').prependTo($anchor);
    $('<span></span>').html(hit.fields.title[0]).appendTo($anchor);
    $anchor.appendTo($row);
    return $row;
}

function queryData(size, from) {
    return {
        from: from,
        size: size,
        sort: ['_uid'],
        fields: ['title']
    };
}

// accessable variables in this scope
var window, document, ARGS, $, jQuery, moment, kbn;

return function(callback) {

    // Setup some variables
    var dashboard, timspan;

    // Set a default timespan if one isn't specified
    timspan = '1d';

    // Intialize a skeleton with nothing but a rows array and service object
    dashboard = {
        rows : [],
        services : {}
    };

    // Set a title
    dashboard.style = 'light';
    dashboard.title = 'Cloud Dashboard Index';
    dashboard.time = {
        from: "now-" + (ARGS.from || timspan),
        to: "now"
    };

    var $content = $('<div></div>');
    var $container = $('<div class="search-results-container"></div>')
        .css('height', 'auto');
    $content.append($container);

    var so_far = 0;

    function success(result) {
        if (result.hits.total > 0) {
            for (var i = 0; i < result.hits.hits.length; i++) {
                $container.append(dashboard_row(result.hits.hits[i]));
            }
            so_far += result.hits.hits.length;
        }
        if (so_far < result.hits.total) {
            get_more(150, so_far);
    }
    else {
            finish();
        }
    }

    function failure(jqXHR, textStatus) {
        $container.html("OOPS. I didn't find any dashboards in the database.");
        finish();
    }

    function get_more(size, start) {
        $.ajax({
            method: 'POST',
            url: '/elasticsearch/grafana-dash/dashboard/_search',
            data: JSON.stringify(queryData(size, start))
        })
        .done(success)
        .fail(failure);
    }

    function finish() {
        row = create_row($content);
        if (dashboard.rows.length > 0) {
            dashboard.rows[0] = row;
        }
        else {
            dashboard.rows.push(row);
        }
        callback(dashboard);
    }

    get_more(150, 0);
}
