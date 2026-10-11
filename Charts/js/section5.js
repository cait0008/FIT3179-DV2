// Section 5: Why? Connection, cost or skills?
// Replace null with the spec path once a chart is built, e.g. embedChart('id', 'Charts/specs/file.vl.json');

embedChart('vis-s5-heatmap',          'Charts/specs/s5_heatmap.vl.json');

// Small multiples: a Vega-Lite facet can't use "width": "container", so size the three panels to fill the box here
fetch('Charts/specs/s5_small_multiples.vl.json').then(function (r) { return r.json(); }).then(function (spec) {
  var box = document.getElementById('vis-s5-small-multiples').clientWidth;
  var panel = Math.floor((box - 2 * chartConfig.padding - 2 * spec.spacing) / 3); // minus chart padding and the gaps between panels
  var k = Math.min(1, panel / 350); // shrink the maps only if a panel is narrower than the 350px the spec was set up for
  var p = spec.spec.projection;
  spec.spec.width = panel;
  spec.spec.height = Math.round(300 * k);
  p.scale = p.scale * k;
  p.translate = [p.translate[0] * k + (panel - 350 * k) / 2, p.translate[1] * k]; // keep each map centred in its panel
  embedChart('vis-s5-small-multiples', spec);
});
embedChart('vis-s5-divergence',       'Charts/specs/s5_divergence.vl.json');
embedChart('vis-s5-slope',            'Charts/specs/s5_slope.vl.json');
embedChart('vis-s5-barriers',         'Charts/specs/s5_barriers.vl.json');
