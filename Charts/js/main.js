// Shared chart setup. Loaded before the section files (section2.js ... section6.js),
// which call embedChart() for each of their charts.

var chartConfig = {
  background: '#FFFFFF', // same as the section cards (--card in styles.css), so charts sit seamlessly inside them
  padding: 16,
  autosize: { type: 'fit', contains: 'padding' }, // keep the padding inside the container, so charts don't overflow
  font: 'Atkinson Hyperlegible Next',
  view: { stroke: null },
  title: { font: 'Oxanium', color: '#25212E' },
  axis: {
    labelColor: '#5F566E',
    titleColor: '#25212E',
    labelFontSize: 12,
    titleFontSize: 13,
    domainColor: '#A79FB6',
    tickColor: '#A79FB6',
    gridColor: '#DCCBE0'
  },
  legend: { labelColor: '#5F566E', titleColor: '#25212E', labelFontSize: 12, titleFontSize: 13 },
  header: { labelColor: '#25212E', labelFont: 'Oxanium', labelFontSize: 13 } // small-multiple panel labels
};

// Embed one chart into the element with this id (from index.html).
// spec: path to a file in Charts/specs/ (relative to index.html), or null to show a placeholder.
// Use *.vl.json for Vega-Lite specs and *.vg.json for full Vega specs (vegaEmbed detects which).
// Returns the vegaEmbed promise, so a section file can use result.view (e.g. to link two charts).
function embedChart(id, spec) {
  var el = document.getElementById(id);

  if (!spec) {
    el.innerHTML = '<div class="vis-placeholder">Chart coming soon</div>';
    return Promise.resolve(null);
  }

  // wait for the web fonts, otherwise Vega measures labels in a fallback font and long ones get clipped
  var embed = document.fonts.ready.then(function () {
    // fixed-size charts (class vis-auto) are drawn as SVG so CSS can scale them to the box width
    var renderer = el.classList.contains('vis-auto') ? 'svg' : 'canvas';
    return vegaEmbed('#' + id, spec, { actions: false, config: chartConfig, renderer: renderer });
  });
  embed.catch(console.error);
  return embed;
}
