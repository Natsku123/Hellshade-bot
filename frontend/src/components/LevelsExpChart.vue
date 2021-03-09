<script>
import { Line, mixins } from "vue-chartjs";
import { gql } from "graphql-request";
import { client, hexToRGB } from "@/utils";
const { reactiveData } = mixins;

export default {
  extends: Line,
  name: "LevelsExpChart",
  mixins: [reactiveData],
  props: ["options", "range"],
  data: () => ({
    rawData: {}
  }),
  watch: {
    range: function(value) {
      let tempLevels = this.rawData["levels"];
      tempLevels = tempLevels.slice(value[0], value[1]);
      this.chartdata.datasets[0].data = [];
      this.chartdata.labels = [];
      tempLevels.forEach(point => {
        this.chartdata.labels.push("Level " + point.x);
        this.chartdata.datasets[0].data.push(point.y);
      });
      let tempMembers = this.rawData["members"];
      tempMembers = tempMembers.slice(value[0], value[1]);
      this.chartdata.datasets[1].data = tempMembers;
      this.$data._chart.update();
    }
  },
  methods: {},
  mounted() {
    const query = gql`
      {
        allLevels {
          edges {
            node {
              uuid
              value
              exp
            }
          }
        }
      }
    `;
    this.gradient = this.$refs.canvas
      .getContext("2d")
      .createLinearGradient(0, 0, 0, 450);
    this.gradient2 = this.$refs.canvas
      .getContext("2d")
      .createLinearGradient(0, 0, 0, 450);
    this.gradient.addColorStop(
      0,
      hexToRGB(this.$vuetify.theme.currentTheme.primary, 0.5)
    ); // 0.5
    this.gradient.addColorStop(
      0.5,
      hexToRGB(this.$vuetify.theme.currentTheme.primary, 0.25)
    ); // 0.25
    this.gradient.addColorStop(
      1,
      hexToRGB(this.$vuetify.theme.currentTheme.primary, 0)
    ); // 0

    this.gradient2.addColorStop(
      0,
      hexToRGB(this.$vuetify.theme.currentTheme.accent, 0.9)
    ); // 0.9
    this.gradient2.addColorStop(
      0.5,
      hexToRGB(this.$vuetify.theme.currentTheme.accent, 0.25)
    ); // 0.25
    this.gradient2.addColorStop(
      1,
      hexToRGB(this.$vuetify.theme.currentTheme.accent, 0)
    ); // 0
    this.chartdata = {
      labels: [],
      datasets: [
        {
          label: "Experience needed",
          showLine: true,
          data: [],
          type: "line",
          yAxisID: "A",
          backgroundColor: this.gradient,
          borderColor: this.$vuetify.theme.currentTheme.primary,
          pointBackgroundColor: this.$vuetify.theme.currentTheme.primary,
          borderWidth: 1,
          pointBorderColor: this.$vuetify.theme.currentTheme.primary
        },
        {
          label: "Players",
          type: "bar",
          yAxisID: "B",
          data: [],
          backgroundColor: this.gradient2
        }
      ]
    };

    // Get all levels
    client
      .request(query)
      .then(data => {
        let temp = [];
        data["allLevels"]["edges"].forEach(n => {
          n.node.uuid = n.node.uuid.substring(1, n.node.uuid.length - 1);
          temp.push({
            x: n.node.value,
            y: n.node.exp
          });
        });
        temp.sort((a, b) => {
          if (a.x < b.x) {
            return -1;
          } else if (a.x > b.x) {
            return 1;
          } else {
            return 0;
          }
        });
        this.rawData["levels"] = temp;
        temp = temp.slice(this.range[0], this.range[1]);
        temp.forEach(point => {
          this.chartdata.labels.push("Level " + point.x);
          this.chartdata.datasets[0].data.push(point.y);
        });
      })
      // Load member data
      .then(() => {
        const membersQuery = gql`
          {
            allMembers {
              edges {
                node {
                  uuid
                  level {
                    value
                    exp
                  }
                }
              }
            }
          }
        `;
        client
          .request(membersQuery)
          .then(data => {
            let temp = {};
            let tempArr = [];
            let max = 0;
            data["allMembers"]["edges"].forEach(n => {
              n.node.uuid = n.node.uuid.substring(1, n.node.uuid.length - 1);

              // Calculate number of players on each level
              if (n.node.level !== null) {
                if (temp[n.node.level.value]) {
                  temp[n.node.level.value]++;
                } else {
                  temp[n.node.level.value] = 1;
                }

                if (temp[n.node.level.value] - 1 > max) {
                  max = temp[n.node.level.value] + 1;
                }
              }
            });
            this.options.scales.yAxes[1].ticks.max = max;
            this.chartdata.labels.forEach(label => {
              const levelValue = Number(label.split(" ")[1]);
              if (temp[levelValue]) {
                tempArr.push(temp[levelValue]);
              } else {
                tempArr.push(0);
              }
            });

            this.rawData["members"] = tempArr;
            tempArr = tempArr.slice(this.range[0], this.range[1]);
            this.chartdata.datasets[1].data = tempArr;
          })
          // Render Chart
          .then(() => {
            this.renderChart(this.chartdata, this.options);
          });
      });
  }
};
</script>

<style scoped></style>
