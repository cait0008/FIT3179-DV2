// Map each chart container (id in index.html) to its spec file in Charts/specs/ (paths are relative to index.html).
// Leave a spec as null until it's built; the page shows a placeholder box instead.
// Use *.vl.json for Vega-Lite specs and *.vg.json for full Vega specs (vegaEmbed detects which).
var charts = {
  // Section 2: Quick comparison
  'vis-s2-waffle':          null, // 'Charts/specs/s2_waffle.vl.json'
  'vis-s2-unit':            null, // 'Charts/specs/s2_unit.vl.json'

  // Section 3: Geography of these scores
  'vis-s3-choro-remote':    null, // 'Charts/specs/s3_choro_remote.vl.json'
  'vis-s3-choro-lga':       null, // 'Charts/specs/s3_choro_lga.vl.json'
  'vis-s3-bivariate':       null, // 'Charts/specs/s3_bivariate.vl.json'
  'vis-s3-dorling':         null, // 'Charts/specs/s3_dorling.vg.json'  (force layout -> Vega)
  'vis-s3-prop-symbol':     null, // 'Charts/specs/s3_prop_symbol.vl.json'
  'vis-s3-beeswarm':        null, // 'Charts/specs/s3_beeswarm.vg.json' (force layout -> Vega)

  // Section 4: Exploring the minorities that face this divide
  'vis-s4-dumbbell':        null, // 'Charts/specs/s4_dumbbell.vl.json'
  'vis-s4-heatmap':         null, // 'Charts/specs/s4_heatmap.vl.json'
  'vis-s4-diverging':       null, // 'Charts/specs/s4_diverging.vl.json'
  'vis-s4-range':           null, // 'Charts/specs/s4_range.vl.json'

  // Section 5: Compounds
  'vis-s5-small-multiples': null, // 'Charts/specs/s5_small_multiples.vl.json'
  'vis-s5-dual-slope':      null, // 'Charts/specs/s5_dual_slope.vl.json'
  'vis-s5-slope':           null, // 'Charts/specs/s5_slope.vl.json'
  'vis-s5-barriers':        null, // 'Charts/specs/s5_barriers.vl.json'

  // Section 6: Is the gap closing?
  'vis-s6-bump':            null, // 'Charts/specs/s6_bump.vl.json'
  'vis-s6-gap':             null  // 'Charts/specs/s6_gap.vl.json'
};

Object.keys(charts).forEach(function (id) {
  var el = document.getElementById(id);
  var spec = charts[id];

  if (!spec) {
    el.innerHTML = '<div class="vis-placeholder">Chart coming soon</div>';
    return;
  }

  vegaEmbed('#' + id, spec, { actions: false }).catch(console.error);
});
