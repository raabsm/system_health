
$().ready(function() {



//=====================================================================================================================//
    var user_count;
    var policy_count;
    var revenue_today;
    var total_revenue;

    function add_timestamp(element, timestamp){
        var to_insert = "<div> <p style=\"color: #5743AF\"><i class=\"fa fa-history\"></i>"
                + " No change in count since "+ timestamp + "</p> </div>";
        element.innerHTML = to_insert;
    }

    function fill_counter_widget(element, counter, sub_counter, title, sub_title){
        var to_insert = "<br><p style=\"color: #5743AF\">" + title + "<h1 style=\"color: #5743AF\">"
             + counter + "</h1></p>";
        if(sub_counter != null){
            to_insert += "<p style=\"color: #5743AF\">" + sub_title
             + "<h2 style=\"color: #5743AF\">" + sub_counter + "</h2></p>";
        }
        element.innerHTML = to_insert;
    }

    function profiles() {
        $.getJSON("/profiles", function(result){
            fill_counter_widget(document.getElementById("num_users"),
                                result['total_profiles'],
                                result['total_last_week'],
                                "Total User Count",
                                "Joined in last 7 days:");
            add_timestamp(document.getElementById("user_stats"), result['most_recently_added']);
        });
    };

    function policies() {
        $.getJSON("/policies", function(result){
            fill_counter_widget(document.getElementById("num_policies"),
                                result['total_policies'],
                                null,
                                "Total Policy Count:",
                                null);

            add_timestamp(document.getElementById("policy_stats"), result['most_recently_added']);
        });
    };

    function revenue() {
        $.getJSON("/revenue", function(result){
             fill_counter_widget(document.getElementById("revenue"),
                                result['total_revenue'],
                                result['revenue_today'],
                                "Total Revenue:",
                                "Revenue Today:");

            add_timestamp(document.getElementById("revenue_stats"), result['most_recently_added']);
        });
    };

    function errors() {
        $.getJSON("/errors", function(result){
             fill_counter_widget(document.getElementById("errors_24_hours"),
                                result['count_last_day'],
                                null,
                                "Errors Last 24 Hours:",
                                null);
             fill_counter_widget(document.getElementById("errors_last_week"),
                                result['count_last_week'],
                                null,
                                "Errors Last 7 Days:",
                                null);
             fill_counter_widget(document.getElementById("errors_last_month"),
                                result['count_last_month'],
                                null,
                                "Errors Last Month:",
                                null);
             fill_error_widgets(result['most_recent_logs']);
        });
    };

    function fill_error_widgets(errors) {
        document.getElementById("error_logs").innerHTML = ""
        var len = errors.length;
        var i;
        for(i=0; i < len; i++) {
            var inner_text = "";
            var error = errors[i];
            for(var key in error) {``
                inner_text += "<p style=\"color: #ff0000 \"><b>" + key + ":</b> " + error[key] + "</p>";
            }
            $("#error_logs").append("<div class=\"col-md-4\"><div class=\"card \"><div class=\"card-body\">" +
            inner_text + "</div></div></div>");
        }
    }

    profiles();
    policies();
    revenue();
    errors();

    setInterval( function() {
        profiles();
        policies();
        revenue();
        errors();
    }, 5000);

    setInterval(function() {
        $('#f1_card').toggleClass("transformStyle transformRotate");
    }, 3000);

//=====================================================================================================================//

    //api pings
    function ping() {
        $.getJSON("/api", function(data){
            var apis = data['api'];
            var i;
            var result = "";
            for (i = 0; i < apis.length; i++) {

                if (apis[i]['info']['active']) {
                    var sign = "<i class=\"fa fa-circle text-success\"></i>";
                }
                else {
                    var sign = "<i class=\"fa fa-circle text-danger\"></i>";
                }

                var response_time = apis[i]['info']['response_time'];
                response_time = parseFloat(response_time).toFixed(2);
                response_time = response_time.toString();

                result = result + "<div class=\"col-md-2\"> <div class=\"card \"> <div class=\"card-body\">" +
                 "<div class=\"widget\" id=\"api\"><h3>" + apis[i]['name'] + "</h3><p>Response time:<br>"+ response_time + " seconds</p>" + sign +
                 "</div></div></div></div>";
            }
            var current_datetime = new Date();
            var hh = current_datetime.getHours()
            var mm = current_datetime.getMinutes()
            var ss = current_datetime.getSeconds()
            if (hh < 10) {hh = "0"+hh;}
            if (mm < 10) {mm = "0"+mm;}
            if (ss < 10) {ss = "0"+ss;}
            var today_string = hh+":"+mm+":"+ss;

            document.getElementById("ping").innerHTML = result + "<div"
            + "style=\"display: block; height: 25px; text-align:center; line-height:25px;\">API Widgets last updated "
            + today_string + "</div>";
        })};

    ping();
    setInterval(function() {
        ping();
    }, 60000);

//=====================================================================================================================//

    $sidebar = $('.sidebar');
    $sidebar_img_container = $sidebar.find('.sidebar-background');

    $full_page = $('.full-page');

    $sidebar_responsive = $('body > .navbar-collapse');

    window_width = $(window).width();

    fixed_plugin_open = $('.sidebar .sidebar-wrapper .nav li.active a p').html();

    if (window_width > 767 && fixed_plugin_open == 'Dashboard') {
        if ($('.fixed-plugin .dropdown').hasClass('show-dropdown')) {
            $('.fixed-plugin .dropdown').addClass('show');
        }

    }

    $('.fixed-plugin a').click(function(event) {
        // Alex if we click on switch, stop propagation of the event, so the dropdown will not be hide, otherwise we set the  section active
        if ($(this).hasClass('switch-trigger')) {
            if (event.stopPropagation) {
                event.stopPropagation();
            } else if (window.event) {
                window.event.cancelBubble = true;
            }
        }
    });

    $('.fixed-plugin .background-color span').click(function() {
        $(this).siblings().removeClass('active');
        $(this).addClass('active');

        var new_color = $(this).data('color');

        if ($sidebar.length != 0) {
            $sidebar.attr('data-color', new_color);
        }

        if ($full_page.length != 0) {
            $full_page.attr('filter-color', new_color);
        }

        if ($sidebar_responsive.length != 0) {
            $sidebar_responsive.attr('data-color', new_color);
        }
    });

    $('.fixed-plugin .img-holder').click(function() {
        $full_page_background = $('.full-page-background');

        $(this).parent('li').siblings().removeClass('active');
        $(this).parent('li').addClass('active');


        var new_image = $(this).find("img").attr('src');

        if ($sidebar_img_container.length != 0 && $('.switch-sidebar-image input:checked').length != 0) {
            $sidebar_img_container.fadeOut('fast', function() {
                $sidebar_img_container.css('background-image', 'url("' + new_image + '")');
                $sidebar_img_container.fadeIn('fast');
            });
        }

        if ($full_page_background.length != 0 && $('.switch-sidebar-image input:checked').length != 0) {
            var new_image_full_page = $('.fixed-plugin li.active .img-holder').find('img').data('src');

            $full_page_background.fadeOut('fast', function() {
                $full_page_background.css('background-image', 'url("' + new_image_full_page + '")');
                $full_page_background.fadeIn('fast');
            });
        }

        if ($('.switch-sidebar-image input:checked').length == 0) {
            var new_image = $('.fixed-plugin li.active .img-holder').find("img").attr('src');
            var new_image_full_page = $('.fixed-plugin li.active .img-holder').find('img').data('src');

            $sidebar_img_container.css('background-image', 'url("' + new_image + '")');
            $full_page_background.css('background-image', 'url("' + new_image_full_page + '")');
        }

        if ($sidebar_responsive.length != 0) {
            $sidebar_responsive.css('background-image', 'url("' + new_image + '")');
        }
    });

    $('.switch input').on("switchChange.bootstrapSwitch", function() {

        $full_page_background = $('.full-page-background');

        $input = $(this);

        if ($input.is(':checked')) {
            if ($sidebar_img_container.length != 0) {
                $sidebar_img_container.fadeIn('fast');
                $sidebar.attr('data-image', '#');
            }

            if ($full_page_background.length != 0) {
                $full_page_background.fadeIn('fast');
                $full_page.attr('data-image', '#');
            }

            background_image = true;
        } else {
            if ($sidebar_img_container.length != 0) {
                $sidebar.removeAttr('data-image');
                $sidebar_img_container.fadeOut('fast');
            }

            if ($full_page_background.length != 0) {
                $full_page.removeAttr('data-image', '#');
                $full_page_background.fadeOut('fast');
            }

            background_image = false;
        }
    });
});

type = ['primary', 'info', 'success', 'warning', 'danger'];


demo = {

//https://stackoverflow.com/questions/9058801/flip-div-with-two-sides-of-html
//https://www.w3schools.com/howto/tryit.asp?filename=tryhow_css_flip_card

    initPickColor: function() {
        $('.pick-class-label').click(function() {
            var new_class = $(this).attr('new-class');
            var old_class = $('#display-buttons').attr('data-class');
            var display_div = $('#display-buttons');
            if (display_div.length) {
                var display_buttons = display_div.find('.btn');
                display_buttons.removeClass(old_class);
                display_buttons.addClass(new_class);
                display_div.attr('data-class', new_class);
            }
        });
    },

    initDocumentationCharts: function() {
        /* ----------==========     Daily Sales Chart initialization For Documentation    ==========---------- */

        dataDailySalesChart = {
            labels: ['M', 'T', 'W', 'T', 'F', 'S', 'S'],
            series: [
                [12, 17, 7, 17, 23, 18, 38]
            ]
        }

        optionsDailySalesChart = {
            lineSmooth: Chartist.Interpolation.cardinal({
                tension: 0
            }),
            low: 0,
            high: 50, // creative tim: we recommend you to set the high sa the biggest value + something for a better look
            chartPadding: {
                top: 0,
                right: 0,
                bottom: 0,
                left: 0
            },
        }

        var dailySalesChart = new Chartist.Line('#dailySalesChart', dataDailySalesChart, optionsDailySalesChart);

        // lbd.startAnimationForLineChart(dailySalesChart);
    },


//=====================================================================================================================/

    initDashboardPageCharts: function() {
        $.getJSON("/graphs", function(response){


            var dict = response['graphs'];

            for(var key in dict) {

            var val = dict[key];

            var info = val['data'].reverse();
            var data_labels = [];
            var data_series = [[], [], []];
            var j;

            for (j = 0; j < info.length; j++) {
                data_labels[j] = info[j]["x"];
                data_series[0][j] = info[j]["y1"];
                if("y2" in info[j]) {
                    data_series[1][j] = info[j]["y2"];
                }
                if("y3" in info[j]) {
                    data_series[2][j] = info[j]["y3"];
                }
            }

            var data = {labels: data_labels, series: data_series};

            var options = {
                seriesBarDistance: 10,
                axisX: {
                    showGrid: false
                },
                height: "245px"
            };

            var responsiveOptions = [
                ['screen and (max-width: 640px)', {
                    seriesBarDistance: 5,
                    axisX: {
                        labelInterpolationFnc: function(value) {
                            return value[0];
                        }
                    }
                }]
            ];

            var second_val = "";
            var third_val = "";
            if('y2' in val['key']) {
                second_val = "<i class=\"fa fa-circle text-danger\"></i>" + val['key']['y2'];
            }
            if('y3' in val['key']) {
                third_val = "<i class=\"fa fa-circle text-warning\"></i>" + val['key']['y3'];
            }


            var id = "chartActivity" + key;
            $("#bar-charts").append("<div class=\"col-md-6\"><div class=\"card \">" +
            "<div class=\"card-header \"><h4 class=\"card-title\">" + val['title'] +"</h4></div><div class=\"card-body \" id=\"chart\">"+
            "<div id=\"" + id + "\" class=\"ct-chart\"></div></div><br><div class=\"card-footer \">" +
            "<i class=\"fa fa-circle text-info\"></i>" + val['key']['y1'] + second_val + third_val + "<hr>" +
            "<div class=\"stats\"><i class=\"fa fa-check\"></i> Data information certified</div>" +
            "</div></div></div>");
            id = "#" + id;
            var chartActivity = Chartist.Bar(id, data, options, responsiveOptions);
            }

            var dataPreferences = {
                series: [
                    [25, 30, 20, 25]
                ]
            };

            var optionsPreferences = {
                donut: true,
                donutWidth: 40,
                startAngle: 0,
                total: 100,
                showLabel: false,
                axisX: {
                    showGrid: false
                }
            };

    //    if (i=1){
            Chartist.Pie('#chartPreferences', dataPreferences, optionsPreferences);

            Chartist.Pie('#chartPreferences', {
                labels: ['53%', '36%', '11%'],
                series: [53, 36, 11]
            });
    //    }


            var dataSales = {
                labels: ['00:00', '03:00', '06:00', '09:00', '12:00', '15:00', '18:00', '21:00'],
                series: [
                    [500, 385, 490, 492, 554, 586, 698, 695, 752, 788, 846, 944]
                ]
            };

            // var optionsSales = {
            //   lineSmooth: false,
            //   low: 0,
            //   high: 800,
            //    chartPadding: 0,
            //   showArea: true,
            //   height: "245px",
            //   axisX: {
            //     showGrid: false,
            //   },
            //   axisY: {
            //     showGrid: false,
            //   },
            //   lineSmooth: Chartist.Interpolation.simple({
            //     divisor: 6
            //   }),
            //   showLine: false,
            //   showPoint: true,
            //   fullWidth: true
            // };
            var optionsSales = {
                lineSmooth: false,
                low: 0,
                high: 800,
                showArea: true,
                height: "245px",
                axisX: {
                    showGrid: false,
                },
                lineSmooth: Chartist.Interpolation.simple({
                    divisor: 3
                }),
                showLine: false,
                showPoint: false,
                fullWidth: false
            };

            var responsiveSales = [
                ['screen and (max-width: 640px)', {
                    axisX: {
                        labelInterpolationFnc: function(value) {
                            return value[0];
                        }
                    }
                }]
            ];

    //        if(i=1){
                var chartHours = Chartist.Line('#chartHours', dataSales, optionsSales, responsiveSales);
    //        }

            // lbd.startAnimationForLineChart(chartHours);
//-->
            // lbd.startAnimationForBarChart(chartActivity);

            // /* ----------==========     Daily Sales Chart initialization    ==========---------- */
            //
            // dataDailySalesChart = {
            //     labels: ['M', 'T', 'W', 'T', 'F', 'S', 'S'],
            //     series: [
            //         [12, 17, 7, 17, 23, 18, 38]
            //     ]
            // };
            //
            // optionsDailySalesChart = {
            //     lineSmooth: Chartist.Interpolation.cardinal({
            //         tension: 0
            //     }),
            //     low: 0,
            //     high: 50, // creative tim: we recommend you to set the high sa the biggest value + something for a better look
            //     chartPadding: { top: 0, right: 0, bottom: 0, left: 0},
            // }
            //
            // var dailySalesChart = Chartist.Line('#dailySalesChart', dataDailySalesChart, optionsDailySalesChart);

            // lbd.startAnimationForLineChart(dailySalesChart);

            //
            //
            // /* ----------==========     Completed Tasks Chart initialization    ==========---------- */
            //
            // dataCompletedTasksChart = {
            //     labels: ['12am', '3pm', '6pm', '9pm', '12pm', '3am', '6am', '9am'],
            //     series: [
            //         [230, 750, 450, 300, 280, 240, 200, 190]
            //     ]
            // };
            //
            // optionsCompletedTasksChart = {
            //     lineSmooth: Chartist.Interpolation.cardinal({
            //         tension: 0
            //     }),
            //     low: 0,
            //     high: 1000, // creative tim: we recommend you to set the high sa the biggest value + something for a better look
            //     chartPadding: { top: 0, right: 0, bottom: 0, left: 0}
            // }
            //
            // var completedTasksChart = new Chartist.Line('#completedTasksChart', dataCompletedTasksChart, optionsCompletedTasksChart);
            //
            // // start animation for the Completed Tasks Chart - Line Chart
            // lbd.startAnimationForLineChart(completedTasksChart);
            //
            //
            // /* ----------==========     Emails Subscription Chart initialization    ==========---------- */
            //
            // var dataEmailsSubscriptionChart = {
            //   labels: ['Jan', 'Feb', 'Mar', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            //   series: [
            //     [542, 443, 320, 780, 553, 453, 326, 434, 568, 610, 756, 895]
            //
            //   ]
            // };
            // var optionsEmailsSubscriptionChart = {
            //     axisX: {
            //         showGrid: false
            //     },
            //     low: 0,
            //     high: 1000,
            //     chartPadding: { top: 0, right: 5, bottom: 0, left: 0}
            // };
            // var responsiveOptions = [
            //   ['screen and (max-width: 640px)', {
            //     seriesBarDistance: 5,
            //     axisX: {
            //       labelInterpolationFnc: function (value) {
            //         return value[0];
            //       }
            //     }
            //   }]
            // ];
            // var emailsSubscriptionChart = Chartist.Bar('#emailsSubscriptionChart', dataEmailsSubscriptionChart, optionsEmailsSubscriptionChart, responsiveOptions);
            //
            // //start animation for the Emails Subscription Chart
            // lbd.startAnimationForBarChart(emailsSubscriptionChart);


        });
        }
//
//    initGoogleMaps: function() {
//        var myLatlng = new google.maps.LatLng(40.748817, -73.985428);
//        var mapOptions = {
//            zoom: 13,
//            center: myLatlng,
//            scrollwheel: false, //we disable de scroll over the map, it is a really annoing when you scroll through page
//            styles: [{
//                "featureType": "water",
//                "elementType": "geometry",
//                "stylers": [{
//                    "color": "#e9e9e9"
//                }, {
//                    "lightness": 17
//                }]
//            }, {
//                "featureType": "landscape",
//                "elementType": "geometry",
//                "stylers": [{
//                    "color": "#f5f5f5"
//                }, {
//                    "lightness": 20
//                }]
//            }, {
//                "featureType": "road.highway",
//                "elementType": "geometry.fill",
//                "stylers": [{
//                    "color": "#ffffff"
//                }, {
//                    "lightness": 17
//                }]
//            }, {
//                "featureType": "road.highway",
//                "elementType": "geometry.stroke",
//                "stylers": [{
//                    "color": "#ffffff"
//                }, {
//                    "lightness": 29
//                }, {
//                    "weight": 0.2
//                }]
//            }, {
//                "featureType": "road.arterial",
//                "elementType": "geometry",
//                "stylers": [{
//                    "color": "#ffffff"
//                }, {
//                    "lightness": 18
//                }]
//            }, {
//                "featureType": "road.local",
//                "elementType": "geometry",
//                "stylers": [{
//                    "color": "#ffffff"
//                }, {
//                    "lightness": 16
//                }]
//            }, {
//                "featureType": "poi",
//                "elementType": "geometry",
//                "stylers": [{
//                    "color": "#f5f5f5"
//                }, {
//                    "lightness": 21
//                }]
//            }, {
//                "featureType": "poi.park",
//                "elementType": "geometry",
//                "stylers": [{
//                    "color": "#dedede"
//                }, {
//                    "lightness": 21
//                }]
//            }, {
//                "elementType": "labels.text.stroke",
//                "stylers": [{
//                    "visibility": "on"
//                }, {
//                    "color": "#ffffff"
//                }, {
//                    "lightness": 16
//                }]
//            }, {
//                "elementType": "labels.text.fill",
//                "stylers": [{
//                    "saturation": 36
//                }, {
//                    "color": "#333333"
//                }, {
//                    "lightness": 40
//                }]
//            }, {
//                "elementType": "labels.icon",
//                "stylers": [{
//                    "visibility": "off"
//                }]
//            }, {
//                "featureType": "transit",
//                "elementType": "geometry",
//                "stylers": [{
//                    "color": "#f2f2f2"
//                }, {
//                    "lightness": 19
//                }]
//            }, {
//                "featureType": "administrative",
//                "elementType": "geometry.fill",
//                "stylers": [{
//                    "color": "#fefefe"
//                }, {
//                    "lightness": 20
//                }]
//            }, {
//                "featureType": "administrative",
//                "elementType": "geometry.stroke",
//                "stylers": [{
//                    "color": "#fefefe"
//                }, {
//                    "lightness": 17
//                }, {
//                    "weight": 1.2
//                }]
//            }]
//        };
//
//        var map = new google.maps.Map(document.getElementById("map"), mapOptions);
//
//        var marker = new google.maps.Marker({
//            position: myLatlng,
//            title: "Hello World!"
//        });
//
//        // To add the marker to the map, call setMap();
//        marker.setMap(map);
//    },

//    showNotification: function(from, align) {
//        color = Math.floor((Math.random() * 4) + 1);
//
//        $.notify({
//            icon: "nc-icon nc-app",
//            message: "Welcome to <b>Light Bootstrap Dashboard</b> - a beautiful freebie for every web developer."
//
//        }, {
//            type: type[color],
//            timer: 8000,
//            placement: {
//                from: from,
//                align: align
//            }
//        });
//    }



    }