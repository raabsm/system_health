var obj = {"profiles_last_week": [{"date": "04/17",
                         "registered": 54,
                         "filled_profile": 30},

                         {"date": "04/18",
                         "registered": 54,
                         "filled_profile": 30},

                         {"date": "04/19",
                         "registered": 54,
                         "filled_profile": 30}

]}

var data = function(obj) {
    var info = obj["profiles_last_week"]
    var data_labels = [];
    var data_series = [[][]];
    var i;
    for (i = 0; i < info.length; i++) {
        data_labels[i] = info[i]["date"];
        data_series[0][i] = info[i]["registered"];
        data_series[1][i] = info[i]["filled_profile"];
    }
    {labels: data_labels, series: data_series};
}