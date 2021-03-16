/*
Mixin used to provide components / views with reloading capabilities
 */
const reloadMixin = {
  data: () => ({
    interval: null
  }),
  mounted() {
    if (this.loadContent) {
      this.loadContent();

      this.interval = setInterval(() => {
        this.loadContent();
      }, 30000); // Load every 30 seconds
    }
  },
  beforeDestroy() {
    if (this.interval) {
      clearInterval(this.interval);
    }
  }
};

export { reloadMixin };
