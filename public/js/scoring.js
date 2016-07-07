var score = FINAL_SCORE;
var data = function(score)
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
  title:"Score of Conversation"

};
Plotly.newPlot('score', data(score),layout);