var demo = {

  initDashboardPageCharts: function(meteringPointsData) {
    //if (meteringPointsData.length > 0) {
      //console.log("Metering Points Data:", meteringPointsData);


    // Configurationen
    gradientChartOptionsConfiguration =  {
      maintainAspectRatio: false,
      legend: {
            display: false
      },

      tooltips: {
        backgroundColor: '#fff',
        titleFontColor: '#333',
        bodyFontColor: '#666',
        bodySpacing: 4,
        xPadding: 12,
        mode: "nearest",
        intersect: 0,
        position: "nearest"
      },
      responsive: true,
      scales:{
        yAxes: [{
          barPercentage: 1.6,
              gridLines: {
                drawBorder: false,
                  color: 'rgba(29,140,248,0.0)',
                  zeroLineColor: "transparent",
              },
              ticks: {
                suggestedMin:50,
                suggestedMax: 110,
                  padding: 20,
                  fontColor: "#9a9a9a"
              }
            }],

        xAxes: [{
          barPercentage: 1.6,
              gridLines: {
                drawBorder: false,
                  color: 'rgba(220,53,69,0.1)',
                  zeroLineColor: "transparent",
              },
              ticks: {
                  padding: 20,
                  fontColor: "#9a9a9a"
              }
            }]
        }
    };

    var ctx = document.getElementById("chartBig1").getContext("2d");

    var gradientStroke = ctx.createLinearGradient(0,230,0,50);

    gradientStroke.addColorStop(1, 'rgba(72,72,176,0.2)');
    gradientStroke.addColorStop(0.2, 'rgba(72,72,176,0.0)');
    gradientStroke.addColorStop(0, 'rgba(119,52,169,0)'); //purple colors

    var data = {
      labels: ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'],
      datasets: [{
        label: "Data",
        fill: true,
        backgroundColor: gradientStroke,
        borderColor: '#d048b6',
        borderWidth: 2,
        borderDash: [],
        borderDashOffset: 0.0,
        pointBackgroundColor: '#d048b6',
        pointBorderColor:'rgba(255,255,255,0)',
        pointHoverBackgroundColor: '#d048b6',
        pointBorderWidth: 20,
        pointHoverRadius: 4,
        pointHoverBorderWidth: 15,
        pointRadius: 4,
        data: [ 60,110,70,100, 75, 90, 80, 100, 70, 80, 120, 80],
      }]
    };

    var myChart = new Chart(ctx, {
      type: 'line',
      data: data,
      options: gradientChartOptionsConfiguration
    });

    //}else {
        //console.log("No metering points avalibale");
    //}


  }
};







/*
function aggregateData(records, interval = 'day') {
  console.log("Aggregating");
  const aggregatedData = {};
  records.forEach(record => {
      const date = new Date(record.timestamp);
      const key = interval === 'motnh' ? date.toISOString().slice(0, 10) : date.toISOString().slice(0, 7); // daily or monthly
      if (!aggregatedData[key]) {
          aggregatedData[key] = { sum: 0, count: 0 };
      }
      aggregatedData[key].sum += record.consumption_value;
      aggregatedData[key].count += 1;
  });
  return Object.keys(aggregatedData).map(key => ({
      timestamp: key,
      consumption_value: aggregatedData[key].sum / aggregatedData[key].count
  }));
}

var demo = {
initDashboardPageCharts: function(meteringPointsData) {
  if (meteringPointsData.length > 0) {
    console.log("Metering Points Data:", meteringPointsData);

    var pointData = meteringPointsData[0];  // Using the first metering point's data
    var aggregatedData = aggregateData(pointData.records, 'month'); 
    var labels = aggregatedData.map(record => record.timestamp);
    var data = aggregatedData.map(record => record.consumption_value);

    var ctx = document.getElementById("chartBig1").getContext("2d");

    var gradientStroke = ctx.createLinearGradient(0, 230, 0, 50);
    gradientStroke.addColorStop(1, 'rgba(72,72,176,0.1)');
    gradientStroke.addColorStop(0.4, 'rgba(72,72,176,0.0)');
    gradientStroke.addColorStop(0, 'rgba(119,52,169,0)');

    var config = {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: "Consumption Data",
          fill: true,
          backgroundColor: gradientStroke,
          borderColor: '#d346b1',
          borderWidth: 2,
          pointBackgroundColor: '#d346b1',
          pointBorderColor: 'rgba(255,255,255,0)',
          pointHoverBackgroundColor: '#d346b1',
          pointBorderWidth: 2,
          pointHoverRadius: 4,
          pointHoverBorderWidth: 2,
          pointRadius: 2,
          data: data,
        }]
      },
      options: {
        maintainAspectRatio: false,
        legend: {
          display: true,
          position: 'top',
          labels: {
            fontColor: '#9e9e9e'
          }
        },
        tooltips: {
          backgroundColor: '#f5f5f5',
          titleFontColor: '#333',
          bodyFontColor: '#666',
          bodySpacing: 4,
          xPadding: 12,
          mode: "nearest",
          intersect: 0,
          position: "nearest"
        },
        responsive: true,
        scales: {
          yAxes: [{
            stacked: true,  // Enable stacked mode
            gridLines: {
              drawBorder: false,
              color: 'rgba(29,140,248,0.1)',
              zeroLineColor: "transparent",
            },
            ticks: {
              beginAtZero: true,
              padding: 20,
              fontColor: "#9e9e9e"
            }
          }],
          xAxes: [{
            type: 'time',
            time: {
              unit: 'day',
              tooltipFormat: 'll',
              displayFormats: {
                day: 'MMM D'
              }
            },
            gridLines: {
              drawBorder: false,
              color: 'rgba(29,140,248,0.1)',
              zeroLineColor: "transparent",
            },
            ticks: {
              padding: 20,
              fontColor: "#9e9e9e"
            }
          }]
        },
        plugins: {
          zoom: {
            pan: {
              enabled: true,
              mode: 'xy'
            },
            zoom: {
              enabled: true,
              mode: 'xy',
            }
          }
        }
      }
    };

    var myChart = new Chart(ctx, config);
  } else {
    console.log("No metering points data available.");
  }
}
};


*/