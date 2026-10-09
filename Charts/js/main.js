// Shared chart setup. Loaded before the section files (section2.js ... section6.js),
// which call embedChart() for each of their charts.

// Shared look for every chart, so axis labels and legends match the page typography.
// A spec's own "config" overrides these. Leave "title" out of specs: the HTML <h3> is the title.
// In each spec, use "width": "container" and "height": "container" to fill the CSS-sized box.
var chartConfig = {
  background: null, // transparent, so charts sit on the section colour
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

  var embed = vegaEmbed('#' + id, spec, { actions: false, config: chartConfig });
  embed.catch(console.error);
  return embed;
}
