var DataStreamModel = Backbone.Model.extend({
    idAttribute: 'datastream_revision_id',

    url: function () {
        return ['/rest/datastreams/',
            this.get('datastream_revision_id'),
            '/data.json/?limit=50&page=0'].join('');
    },

    initialize: function () {
        this.data = new Backbone.Model();
    },

    parse: function (response) {
        this.response = response;
        var headers = _.filter(response.fArray, function(x){ return x.fHeader; }),
            data = _.filter(response.fArray, function(x){ return !x.fHeader; }),
            rows = _.map(_.range(0, response.fRows), function (i) {
              var row = response.fArray.slice(i*response.fCols, (i+1)*response.fCols);
              return this.formatRow(row);
            }, this);

        this.data.set('headers', _.first(headers, response.fCols))
        this.data.set('columns', _.first(data, response.fCols));
        this.data.set('rows', rows);
    },

    formatRow: function (row) {
        return _.map(row, function (cell) {
            return this.formatCell(cell);
        }, this);
    },

    formatCell: function (cell) {
        var value;

        if (cell.fType === 'TEXT') {
            value = this.formatTEXT(cell);
        } else if (cell.fType === 'DATE') {
            value = this.formatDATE(cell);
        } else if (cell.fType === 'NUMBER') {
            value = this.formatNUMBER(cell);
        } else if (cell.fType === 'LINK') {
            value = this.formatLINK(cell);
        }

        return value;
    },

    formatTEXT: function (cell) {
        var value;
        value = (cell.fStr.length !== 1)? cell.fStr: cell.fStr.replace('-', '&nbsp;');
        value = value.replace(/(<([^>]+)>)/ig," "); // remove html tags from string
        return value;
    },

    formatDATE: function (cell) {
        var value;
        var format = cell.fDisplayFormat;
        var timestamp = cell.fNum;
        if (! _.isUndefined(format)) {
            // sometimes are seconds, sometimes miliseconds
            if (timestamp < 100000000000) {
                timestamp = timestamp * 1000;
            }
            var locale = format.fLocale;
            //One must use "" for "en"
            if (undefined === locale || locale === "en" || locale.indexOf("en_")) {
                locale = "";
            }
            if (locale.indexOf("es_")) {
                locale = "es";
            }

            var dt = new Date(timestamp);
            dt.setTime( dt.getTime() + dt.getTimezoneOffset()*60*1000 );

            value = $.datepicker.formatDate(format.fPattern, dt, {
                dayNamesShort: $.datepicker.regional[locale].dayNamesShort,
                dayNames: $.datepicker.regional[locale].dayNames,
                monthNamesShort: $.datepicker.regional[locale].monthNamesShort,
                monthNames: $.datepicker.regional[locale].monthNames
            });
        } else {
            value = String(timestamp);
        }
        return value;
    },

    formatNUMBER: function (cell) {
        var format = cell.fDisplayFormat,
            number = ( _.isUndefined(format) ) ? cell.fNum : $.formatNumber( cell.fNum, {format:format.fPattern, locale:format.fLocale} );
        return String(number);
    },

    formatLINK: function (cell) {
        var value = '<a target="_blank" href="' + cell.fUri + '" rel="nofollow" title="' + cell.fStr + '">' + cell.fStr + '</a>';
        return value;        
    }
})