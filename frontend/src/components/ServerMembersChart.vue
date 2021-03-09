<script>
import { Bar, mixins } from "vue-chartjs";
import { gql } from "graphql-request";
import { client, hexToRGB } from "@/utils";
const { reactiveData } = mixins;

export default {
  extends: Bar,
  name: "ServerMembersChart",
  mixins: [reactiveData],
  props: ["options"],
  mounted() {
    const query = gql`
      {
        allServers {
          edges {
            node {
              uuid
              name
              members {
                edges {
                  node {
                    uuid
                  }
                }
              }
            }
          }
        }
      }
    `;
    this.gradient = this.$refs.canvas
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
    this.chartdata = {
      labels: [],
      datasets: [
        {
          label: "Members",
          data: [],
          backgroundColor: this.gradient,
          borderColor: this.$vuetify.theme.currentTheme.primary,
          pointBackgroundColor: this.$vuetify.theme.currentTheme.primary,
          borderWidth: 1,
          pointBorderColor: this.$vuetify.theme.currentTheme.primary
        }
      ]
    };
    client
      .request(query)
      .then(data => {
        let temp = {};
        data.allServers.edges.forEach(server => {
          this.chartdata.labels.push(server.node.name);
          server.node.members.edges.forEach(() => {
            if (temp[server.node.name]) {
              temp[server.node.name]++;
            } else {
              temp[server.node.name] = 1;
            }
          });
        });
        this.chartdata.labels.forEach(server => {
          this.chartdata.datasets[0].data.push(temp[server]);
        });
      })
      .then(() => {
        this.renderChart(this.chartdata, this.options);
      });
  }
};
</script>

<style scoped></style>
