const darkColor = "rgba(255,255,255,0.8)";
const darkColor2 = "rgba(255,255,255, 0.5)";
const lightColor = "rgba(0,0,0, 0.8)";
const lightColor2 = "rgba(0,0,0, 0.5)";

/*
Change color based on theme
 */
const axesTheme = (axes, dark) => {
  if (!axes) {
    axes = [{}];
  }
  let n = 1;
  axes.forEach(y => {
    let d;
    let l;
    if (n === 1) {
      d = darkColor;
      l = lightColor;
    } else {
      d = darkColor2;
      l = lightColor2;
    }
    n++;
    if (y.ticks) {
      y.ticks.fontColor = dark ? d : l;
    } else {
      y.ticks = {
        fontColor: dark ? d : l
      };
    }

    if (!y.gridLines) {
      y.gridLines = {
        color: dark ? d : l
      };
    } else {
      y.gridLines.color = dark ? d : l;
    }
  });
  return axes;
};

/*
Mixin for theme changing
 */
const chartThemeMixin = {
  watch: {
    "$vuetify.theme.dark"(newValue) {
      this.refreshTheme(newValue);
    }
  },
  methods: {
    refreshTheme(state) {
      this.options.scales.yAxes = axesTheme(this.options.scales.yAxes, state);
      this.options.scales.xAxes = axesTheme(this.options.scales.xAxes, state);
      if (!this.options.legend) {
        this.options.legend = {
          labels: {
            fontColor: null
          }
        };
      } else if (!this.options.legend.labels) {
        this.options.legend.labels = {};
      }
      this.options.legend.labels.fontColor = state ? darkColor : lightColor;
      this.renderChart(this.chartdata, this.options);
    }
  },
  mounted() {
    this.refreshTheme(this.$vuetify.theme.dark);
  }
};

export { chartThemeMixin };
