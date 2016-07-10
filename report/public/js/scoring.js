$.urlParam = function(name){
    var results = new RegExp('[\?&]' + name + '=([^&#]*)').exec(window.location.href);
    return results[1] || 0;
}

$.get("https://reginag.vishnu.io/get_score/" + $.urlParam('id'), function(response) {

var score = response*10;

var data = function(data)
{
  var bar_color;
if(score<5)
  {
    bar_color = 'rgba(255,0,0,0.6)';
  }
else if(score >=5 && score<7.5)
  {
    bar_color = 'rgba(255,255,0,0.8)';
  }
else
  {
    bar_color = 'rgba(0,255,0,0.6)';
  }

var data = [{
  type: 'bar',
  x: [score],
  y: ['Score'],
  orientation: 'h',
  marker:{
    color: bar_color,
  },
  hoverinfo: 'x',
  tickwidth: "100",
}];
  return data;
};

var layout = {
  xaxis: {range: [0, 10]},
  title:"Confidence Level"

};
Plotly.newPlot('score', data(score),layout); 

});